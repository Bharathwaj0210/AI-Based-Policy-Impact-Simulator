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
            X, used_features = service.safe_feature_subset(df, service.required_features)
            
            # Model Output logic from Streamlit
            df["risk_score"] = service.model.predict_proba(X)[:, 1]
            
            numeric_cols = X.select_dtypes(include="number").columns
            df["claim_severity"] = df["risk_score"] * X[numeric_cols].mean(axis=1)
            
            # ML-Derived Scenarios (qcut from Streamlit)
            if df["risk_score"].nunique() > 1:
                df["case_type"] = pd.qcut(
                    df["risk_score"],
                    q=[0, 0.3, 0.7, 1.0],
                    labels=["Best Case", "Average Case", "Worst Case"],
                    duplicates="drop"
                )
            else:
                df["case_type"] = "Average Case"
            
            # Calculate summary stats for tables
            summary_stats = df.groupby("case_type").agg(
                Records=("risk_score", "count"),
                Avg_Risk=("risk_score", "mean"),
                Avg_Claim_Severity=("claim_severity", "mean")
            ).reset_index().to_dict('records')
            
            total_records = len(df)
            overall_metrics = {
                "records_evaluated": total_records,
                "eligibility_rate": 0.7, # Default 
                "eligible": int(total_records * 0.7),
                "rejected": total_records - int(total_records * 0.7)
            }
            
            # Policy Recommendation from low_risk predictions
            low_risk = df[df["risk_score"] <= df["risk_score"].quantile(0.7)]
            rec = []
            if mapped_type == "health":
                if "age" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"Age ≤ {int(low_risk['age'].quantile(0.9))}")
                if "bmi" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"BMI ≤ {round(low_risk['bmi'].quantile(0.9), 1)}")
                if "smoker" in df.columns:
                    rec.append("Prefer Non-Smokers")
            else:
                if "vehicle_age" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"Vehicle Age ≤ {int(low_risk['vehicle_age'].quantile(0.9))}")
                if "accident_history" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"Accident History ≤ {int(low_risk['accident_history'].quantile(0.9))}")

            return Response({
                "status": "success",
                "data": json.loads(df.to_json(orient='records')),
                "summary": summary_stats,
                "overall_metrics": overall_metrics,
                "used_features": used_features,
                "recommendations": rec
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
            
        try:
            df = pd.DataFrame(data)
            eligible = pd.Series(True, index=df.index)
            
            model_type_map = {"Health Insurance": "health", "Vehicle Insurance": "vehicle"}
            mapped_type = model_type_map.get(insurance_type, "health")
            
            if mapped_type == "health":
                max_age = filters.get("max_age", 60)
                max_bmi = filters.get("max_bmi", 35.0)
                allow_smoker = filters.get("allow_smoker", "Yes")
                
                if "age" in df.columns:
                    eligible &= pd.to_numeric(df["age"], errors="coerce").fillna(0) <= float(max_age)
                if "bmi" in df.columns:
                    eligible &= pd.to_numeric(df["bmi"], errors="coerce").fillna(0) <= float(max_bmi)
                if allow_smoker == "No" and "smoker" in df.columns:
                    eligible &= df["smoker"].astype(str).str.lower().isin(["no", "false", "0"])
            else:
                max_vehicle_age = filters.get("max_vehicle_age", 10)
                max_accidents = filters.get("max_accidents", 2)
                
                if "vehicle_age" in df.columns:
                    eligible &= pd.to_numeric(df["vehicle_age"], errors="coerce").fillna(0) <= float(max_vehicle_age)
                if "accident_history" in df.columns:
                    eligible &= pd.to_numeric(df["accident_history"], errors="coerce").fillna(0) <= float(max_accidents)
            
            eligible_count = int(eligible.sum())
            total_count = len(df)
            
            # Policy Recommendation from low_risk predictions
            low_risk = df[df["risk_score"] <= df["risk_score"].quantile(0.7)]
            rec = []
            if mapped_type == "health":
                if "age" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"Age ≤ {int(low_risk['age'].quantile(0.9))}")
                if "bmi" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"BMI ≤ {round(low_risk['bmi'].quantile(0.9), 1)}")
                if "smoker" in df.columns:
                    rec.append("Prefer Non-Smokers")
            else:
                if "vehicle_age" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"Vehicle Age ≤ {int(low_risk['vehicle_age'].quantile(0.9))}")
                if "accident_history" in low_risk.columns and len(low_risk) > 0:
                    rec.append(f"Accident History ≤ {int(low_risk['accident_history'].quantile(0.9))}")
                    
            return Response({
                "status": "success",
                "eligible_count": eligible_count,
                "rejected_count": total_count - eligible_count,
                "total_count": total_count,
                "recommendations": rec
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class InsuranceExplainView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        filters = request.data.get("filters", {})
        insurance_type = request.data.get("insurance_type", "Health Insurance")
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df = pd.DataFrame(data)
            model_type_map = {"Health Insurance": "health", "Vehicle Insurance": "vehicle"}
            mapped_type = model_type_map.get(insurance_type, "health")
            
            # Apply dynamic filtering
            eligible = pd.Series(True, index=df.index)
            if mapped_type == "health":
                max_age = filters.get("max_age", 60)
                max_bmi = filters.get("max_bmi", 35.0)
                allow_smoker = filters.get("allow_smoker", "Yes")
                if "age" in df.columns:
                    eligible &= pd.to_numeric(df["age"], errors="coerce").fillna(0) <= float(max_age)
                if "bmi" in df.columns:
                    eligible &= pd.to_numeric(df["bmi"], errors="coerce").fillna(0) <= float(max_bmi)
                if allow_smoker == "No" and "smoker" in df.columns:
                    eligible &= df["smoker"].astype(str).str.lower().isin(["no", "false", "0"])
            else:
                max_vehicle_age = filters.get("max_vehicle_age", 10)
                max_accidents = filters.get("max_accidents", 2)
                if "vehicle_age" in df.columns:
                    eligible &= pd.to_numeric(df["vehicle_age"], errors="coerce").fillna(0) <= float(max_vehicle_age)
                if "accident_history" in df.columns:
                    eligible &= pd.to_numeric(df["accident_history"], errors="coerce").fillna(0) <= float(max_accidents)
            
            df_filtered = df[eligible]
            if len(df_filtered) == 0:
                return Response({"status": "success", "shap_data": []})
                
            service = InsurancePredictionService(insurance_type=mapped_type)
            df_shap = df_filtered.head(50)
            X, used_features = service.safe_feature_subset(df_shap, service.required_features)
            
            pipeline = service.model
            preprocessor = pipeline.named_steps["preprocessor"]
            model = pipeline.named_steps["model"]
            
            X_transformed = preprocessor.transform(X)
            if hasattr(X_transformed, "toarray"):
                X_transformed = X_transformed.toarray()

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_transformed)
            
            if isinstance(shap_values, list):
                sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                sv = shap_values[:, :, 1] if shap_values.shape[2] > 1 else shap_values[:, :, 0]
            else:
                sv = shap_values
                
            feature_names = preprocessor.get_feature_names_out()
            n_features = min(len(feature_names), sv.shape[1])
            feature_names = feature_names[:n_features]
            sv_slice = sv[:, :n_features]
            
            shap_importance = np.abs(sv_slice).mean(axis=0)
            
            shap_table = pd.DataFrame({
                "feature": feature_names,
                "importance": shap_importance
            }).sort_values("importance", ascending=False).to_dict('records')
            
            return Response({
                "status": "success",
                "shap_data": shap_table
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class InsuranceGeminiSummaryView(APIView):
    def post(self, request):
        insurance_type = request.data.get("insurance_type", "Health Insurance")
        filters = request.data.get("filters", {})
        metrics = request.data.get("metrics", {})
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not found in environment"}, status=500)
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
You are an expert actuary and insurance risk analyst for the {insurance_type} domain.

Current Policy Thresholds: {filters}
Current Impact Metrics: {metrics}

Provide a concise explanation addressing ONLY these three points:
1. Why the recommended policy thresholds are optimal.
2. The estimated demographic reach (how many applicants will benefit or make use of it).
3. How this specific rule type reduces false claims and limits risk exposure.

AI is used strictly to explain the data insights based on these three points.
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
