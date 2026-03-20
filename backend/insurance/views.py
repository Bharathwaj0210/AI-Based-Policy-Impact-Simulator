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
            
            if mapped_type == "vehicle":
                df = service.preprocess_vehicle(df)
                
            X, used_features = service.align_features(df)
            
            # Model Output logic from Streamlit
            df["risk_score"] = service.model.predict_proba(X)[:, 1]
            
            # Guarded calculation of claim severity
            numeric_cols = list(X.select_dtypes(include=[np.number]).columns)
            if numeric_cols:
                df["claim_severity"] = df["risk_score"] * X[numeric_cols].mean(axis=1)
            else:
                df["claim_severity"] = df["risk_score"] * 0
            
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
            
            threshold = result.get("config", {}).get("threshold", 0.5)
            eligible_mask = df["risk_score"] <= threshold
            eligible_count = int(eligible_mask.sum())
            
            total_records = len(df)
            overall_metrics = {
                "records_evaluated": total_records,
                "eligibility_rate": round(eligible_count / total_records, 4) if total_records > 0 else 0,
                "eligible": eligible_count,
                "rejected": total_records - eligible_count
            }
            
            # Ensure numeric conversion for calculating quantiles safely
            recommendation_cols = ["age", "bmi", "customer_age", "driving_experience", "vehicle_age", "value_vehicle", "cylinder_capacity", "premium"]
            for col in recommendation_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Apply preprocessing for vehicle for recommendation columns if needed
            if mapped_type == "vehicle":
                df = service.preprocess_vehicle(df)
            
            low_risk = df[df["risk_score"] <= df["risk_score"].quantile(0.3)]
            rec = []
            if mapped_type == "health":
                if "age" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['age'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"Age ≤ {int(val)}")
                if "bmi" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['bmi'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"BMI ≤ {round(val, 1)}")
                if "smoker" in df.columns:
                    rec.append("Prefer Non-Smokers")
            else:
                # Necessary Features
                if "customer_age" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['customer_age'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"Customer Age ≤ {int(val)}")
                if "driving_experience" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['driving_experience'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"Min Experience: {int(low_risk['driving_experience'].quantile(0.1))} yrs")
                
                # Optional/Balance Features (only if present)
                if "value_vehicle" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['value_vehicle'].quantile(0.5)
                    if not pd.isna(val):
                        rec.append(f"Med Vehicle Value: {int(val)}")
                if "cylinder_capacity" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['cylinder_capacity'].quantile(0.5)
                    if not pd.isna(val):
                        rec.append(f"Med Cylinder Cap: {int(val)}")
                if "premium" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['premium'].quantile(0.5)
                    if not pd.isna(val):
                        rec.append(f"Target Premium: {int(val)}")

            return Response({
                "status": "success",
                "data": json.loads(df.to_json(orient='records')),
                "summary": summary_stats,
                "overall_metrics": overall_metrics,
                "used_features": used_features,
                "recommendations": rec
            })
        except Exception as e:
            import traceback
            print("ERROR IN InsuranceUploadView:")
            traceback.print_exc()
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
            
            if "risk_score" not in df.columns:
                service = InsurancePredictionService(insurance_type=mapped_type)
                pred_res = service.predict(df)
                if pred_res["status"] == "success":
                    df["risk_score"] = pred_res["predictions"]
                else:
                    return Response({"error": f"Auto-prediction failed: {pred_res['message']}"}, status=500)
            
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
                # Necessary
                max_vehicle_age = filters.get("max_vehicle_age", 15)
                min_experience = filters.get("min_experience", 0)
                max_customer_age = filters.get("max_customer_age", 75)
                
                if "vehicle_age" in df.columns:
                    eligible &= pd.to_numeric(df["vehicle_age"], errors="coerce").fillna(0) <= float(max_vehicle_age)
                if "driving_experience" in df.columns:
                    eligible &= pd.to_numeric(df["driving_experience"], errors="coerce").fillna(0) >= float(min_experience)
                if "customer_age" in df.columns:
                    eligible &= pd.to_numeric(df["customer_age"], errors="coerce").fillna(0) <= float(max_customer_age)
                
                # Optional/Balance (Conditional)
                if "value_vehicle" in df.columns and "max_value_vehicle" in filters:
                    eligible &= pd.to_numeric(df["value_vehicle"], errors="coerce").fillna(0) <= float(filters["max_value_vehicle"])
                if "cylinder_capacity" in df.columns and "max_cylinder_capacity" in filters:
                    eligible &= pd.to_numeric(df["cylinder_capacity"], errors="coerce").fillna(0) <= float(filters["max_cylinder_capacity"])
                if "premium" in df.columns and "max_premium" in filters:
                    eligible &= pd.to_numeric(df["premium"], errors="coerce").fillna(0) <= float(filters["max_premium"])
            
            # Ensure engineered features are present for recommendations
            if mapped_type == "vehicle":
                service = InsurancePredictionService(insurance_type=mapped_type)
                df = service.preprocess_vehicle(df)
            
            eligible_count = int(eligible.sum())
            total_count = len(df)
            
            # Ensure risk_score is numeric for filtering
            if "risk_score" in df.columns:
                df["risk_score"] = pd.to_numeric(df["risk_score"], errors="coerce").fillna(1.0)
            else:
                df["risk_score"] = 1.0 # Default high risk if somehow missing
                
            # Policy Recommendation from low_risk predictions
            # Use 0.3 quantile for consistency with upload view
            low_risk_threshold = df["risk_score"].quantile(0.3)
            if pd.isna(low_risk_threshold):
                low_risk_threshold = 0.3
                
            low_risk = df[df["risk_score"] <= low_risk_threshold]
            rec = []
            if mapped_type == "health":
                if "age" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['age'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"Age ≤ {int(val)}")
                if "bmi" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['bmi'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"BMI ≤ {round(val, 1)}")
                if "smoker" in df.columns:
                    rec.append("Prefer Non-Smokers")
            else:
                if "customer_age" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['customer_age'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"Customer Age ≤ {int(val)}")
                if "driving_experience" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['driving_experience'].quantile(0.9)
                    if not pd.isna(val):
                        rec.append(f"Min Experience: {int(low_risk['driving_experience'].quantile(0.1))} yrs")
                if "value_vehicle" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['value_vehicle'].quantile(0.5)
                    if not pd.isna(val):
                        rec.append(f"Med Vehicle Value: {int(val)}")
                if "cylinder_capacity" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['cylinder_capacity'].quantile(0.5)
                    if not pd.isna(val):
                        rec.append(f"Med Cylinder Cap: {int(val)}")
                if "premium" in low_risk.columns and len(low_risk) > 0:
                    val = low_risk['premium'].quantile(0.5)
                    if not pd.isna(val):
                        rec.append(f"Target Premium: {int(val)}")
                    
            return Response({
                "status": "success",
                "eligible_count": eligible_count,
                "rejected_count": total_count - eligible_count,
                "total_count": total_count,
                "recommendations": rec
            })
        except Exception as e:
            import traceback
            print("ERROR IN InsuranceFilterView:")
            traceback.print_exc()
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
                max_vehicle_age = filters.get("max_vehicle_age", 15)
                min_experience = filters.get("min_experience", 0)
                max_customer_age = filters.get("max_customer_age", 75)
                
                if "vehicle_age" in df.columns:
                    eligible &= pd.to_numeric(df["vehicle_age"], errors="coerce").fillna(0) <= float(max_vehicle_age)
                if "driving_experience" in df.columns:
                    eligible &= pd.to_numeric(df["driving_experience"], errors="coerce").fillna(0) >= float(min_experience)
                if "customer_age" in df.columns:
                    eligible &= pd.to_numeric(df["customer_age"], errors="coerce").fillna(0) <= float(max_customer_age)
            
            df_filtered = df[eligible]
            if len(df_filtered) == 0:
                return Response({"status": "success", "shap_data": []})
                
            service = InsurancePredictionService(insurance_type=mapped_type)
            df_shap = df_filtered.head(50)
            
            # Crucial: Apply preprocessing for vehicle so SHAP sees the right features
            if mapped_type == "vehicle":
                df_shap = service.preprocess_vehicle(df_shap)
                
            X, used_features = service.align_features(df_shap)
            
            pipeline = service.model
            
            # Check if it's a Pipeline or a raw model
            from sklearn.pipeline import Pipeline
            if isinstance(pipeline, Pipeline):
                preprocessor = pipeline.named_steps["preprocessor"]
                model = pipeline.named_steps["model"]
                X_transformed = preprocessor.transform(X)
                if hasattr(X_transformed, "toarray"):
                    X_transformed = X_transformed.toarray()
                feature_names = preprocessor.get_feature_names_out()
            else:
                # Raw model (likely vehicle)
                model = pipeline
                X_transformed = X.values # Use underlying numpy array
                feature_names = X.columns.tolist()

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_transformed)
            
            if isinstance(shap_values, list):
                sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                sv = shap_values[:, :, 1] if shap_values.shape[2] > 1 else shap_values[:, :, 0]
            else:
                sv = shap_values
                
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
            import traceback
            print("ERROR IN InsuranceExplainView:")
            traceback.print_exc()
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
        try:
            # Trying 2.5-flash if others are failing
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""
You are an expert actuary and insurance risk analyst for the {insurance_type} domain.

Current Policy Thresholds: {filters}
Current Impact Metrics: {metrics}

Provide a clear, easy-to-understand explanation of why the ML model suggested this rule.
Structure your response into the following three scenarios:
- **Best Case Scenario**: Explain how this rule performs for clearly low-risk applicants.
- **Average Case Scenario**: Explain the expected performance for typical, moderate-risk applicants.
- **Worst Case Scenario**: Explain how this rule protects the organization from high-risk or outlier claims.

Then, briefly summarize:
1. The demographic reach and applicant impact.
2. How this reduces overall risk exposure.

Keep the language simple and avoid technical jargon. Use bolding and bullet points for readability.
"""
            response = model.generate_content(prompt)
            return Response({
                "status": "success",
                "explanation": response.text
            })
        except Exception as e:
            import traceback
            print("ERROR IN InsuranceGeminiSummaryView:")
            traceback.print_exc()
            return Response({"error": f"Gemini Error: {str(e)}"}, status=500)

class InsurancePolicyListView(APIView):
    def get(self, request):
        policies = InsurancePolicy.objects.all()
        serializer = InsurancePolicySerializer(policies, many=True)
        return Response(serializer.data)
