import os
import json
import pandas as pd
import numpy as np
import shap
import google.generativeai as genai
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from .models import InsurancePolicy
from .serializers import InsurancePolicySerializer
from .services import InsurancePredictionService

class InsuranceUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        insurance_type = request.data.get("insurance_type", "Health Insurance")
        if not file:
            return Response({"error": "No file uploaded"}, status=400)
        
        try:
            df = pd.read_csv(file)
            # Map type to model directory naming
            model_type_map = {
                "Health Insurance": "health",
                "Vehicle Insurance": "vehicle"
            }
            mapped_type = model_type_map.get(insurance_type, "health")
            
            service = InsurancePredictionService(insurance_type=mapped_type)
            result = service.predict(df)
            
            if result.get("status") == "error":
                return Response(result, status=400)
            
            # Reconstruct the processed dataframe for output delivery
            df = service.normalize(df)
            df = service.apply_aliases(df)
            X, _ = service.align_features(df)
            
            # Predict risk and severity
            if hasattr(service.model, "predict_proba"):
                df["risk_score"] = service.model.predict_proba(X)[:, 1]
            else:
                df["risk_score"] = service.model.predict(X)
                
            numeric_cols = X.select_dtypes(include="number").columns
            df["claim_severity"] = df["risk_score"] * X[numeric_cols].mean(axis=1)
            
            df["case_type"] = pd.qcut(
                df["risk_score"],
                q=[0, 0.3, 0.7, 1.0],
                labels=["Best Case", "Average Case", "Worst Case"], 
                duplicates="drop"
            )
            
            # Calculate metrics
            summary_stats = df.groupby("case_type").agg(
                Records=("risk_score", "count"),
                Avg_Risk=("risk_score", "mean"),
                Avg_Claim_Severity=("claim_severity", "mean")
            ).reset_index().to_dict('records')
            
            return Response({
                "status": "success",
                "data": json.loads(df.to_json(orient='records')),
                "summary": summary_stats,
                "used_features": result.get("used_features")
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class InsuranceFilterView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        filters = request.data.get("filters", {})
        insurance_type = request.data.get("insurance_type", "Health Insurance")
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        df = pd.DataFrame(data)
        eligible = pd.Series(True, index=df.index)
        
        if insurance_type == "Health Insurance":
            max_age = filters.get("max_age", 60)
            max_bmi = filters.get("max_bmi", 35.0)
            allow_smoker = filters.get("allow_smoker", "Yes")
            
            if "age" in df.columns:
                eligible &= pd.to_numeric(df["age"], errors="coerce") <= max_age
            if "bmi" in df.columns:
                eligible &= pd.to_numeric(df["bmi"], errors="coerce") <= max_bmi
            if allow_smoker == "No" and "smoker" in df.columns:
                eligible &= df["smoker"].astype(str).str.lower().isin(["no", "false", "0"])
        else:
            max_vehicle_age = filters.get("max_vehicle_age", 10)
            max_accidents = filters.get("max_accidents", 2)
            
            if "vehicle_age" in df.columns:
                eligible &= pd.to_numeric(df["vehicle_age"], errors="coerce") <= max_vehicle_age
            if "accident_history" in df.columns:
                eligible &= pd.to_numeric(df["accident_history"], errors="coerce") <= max_accidents
        
        eligible_count = int(eligible.sum())
        total_count = len(df)
        
        # Policy Recommendation
        low_risk = df[df["risk_score"] <= df["risk_score"].quantile(0.7)]
        rec = []
        if insurance_type == "Health Insurance":
            if "age" in low_risk.columns and len(low_risk) > 0:
                rec.append(f"Age <= {int(low_risk['age'].quantile(0.9))}")
            if "bmi" in low_risk.columns and len(low_risk) > 0:
                rec.append(f"BMI <= {round(low_risk['bmi'].quantile(0.9), 1)}")
            if "smoker" in df.columns:
                rec.append("Prefer Non-Smokers")
        else:
            if "vehicle_age" in low_risk.columns and len(low_risk) > 0:
                rec.append(f"Vehicle Age <= {int(low_risk['vehicle_age'].quantile(0.9))}")
            if "accident_history" in low_risk.columns and len(low_risk) > 0:
                rec.append(f"Accident History <= {int(low_risk['accident_history'].quantile(0.9))}")
                
        return Response({
            "status": "success",
            "eligible_count": eligible_count,
            "rejected_count": total_count - eligible_count,
            "total_count": total_count,
            "recommendations": rec
        })

class InsuranceExplainView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        insurance_type = request.data.get("insurance_type", "Health Insurance")
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df = pd.DataFrame(data)
            model_type_map = {"Health Insurance": "health", "Vehicle Insurance": "vehicle"}
            mapped_type = model_type_map.get(insurance_type, "health")
            service = InsurancePredictionService(insurance_type=mapped_type)
            
            # Create feature matrix for SHAP
            X, _ = service.align_features(df)
            
            pipeline = service.model
            preprocessor = pipeline.named_steps.get("preprocessor")
            model = pipeline.named_steps.get("model")
            
            if not preprocessor or not model:
                # If pipeline structure is different, fallback
                return Response({"error": "Model structure not compatible for SHAP"}, status=500)
                
            X_transformed = preprocessor.transform(X)
            
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_transformed)
            if isinstance(shap_values, list): # For classifiers
                shap_values = shap_values[1]
                
            feature_names = preprocessor.get_feature_names_out()
            n_features = min(len(feature_names), shap_values.shape[1])
            feature_names = feature_names[:n_features]
            shap_values = shap_values[:, :n_features]
            
            shap_importance = np.abs(shap_values).mean(axis=0)
            
            shap_table = pd.DataFrame({
                "Feature": feature_names,
                "Mean_SHAP_Impact": shap_importance,
                "Impact_%": 100 * shap_importance / shap_importance.sum()
            }).sort_values("Impact_%", ascending=False).to_dict('records')
            
            return Response({
                "status": "success",
                "shap_data": shap_table
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class InsuranceGeminiSummaryView(APIView):
    def post(self, request):
        insurance_type = request.data.get("insurance_type", "Health Insurance")
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not found in environment"}, status=500)
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = f"""
        Risk scores are generated by trained machine learning models for the {insurance_type} domain.
        Best, Average, and Worst cases are derived using model percentiles.
        Policy recommendations are calculated only from low-risk predictions.
        AI is used strictly to explain model outputs, not to make decisions.
        Please provide a short business-friendly explanation summarizing this process.
        """
        
        try:
            response = model.generate_content(prompt)
            return Response({
                "status": "success",
                "explanation": response.text
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class InsurancePolicyListView(APIView):
    def get(self, request):
        policies = InsurancePolicy.objects.all()
        serializer = InsurancePolicySerializer(policies, many=True)
        return Response(serializer.data)
