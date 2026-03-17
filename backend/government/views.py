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
from .services import GovernmentPredictionService, POLICY_CONDITIONS

# Helper from Streamlit code
def prepare_model_input(df, policy, required_features):
    X = pd.DataFrame()
    for col in required_features:
        if col == "scheme_type":
            X[col] = policy
        elif col in df.columns:
            X[col] = df[col].copy()
        else:
            if col in ["age", "annual_income", "family_size"]:
                X[col] = np.nan
            elif col in ["disability_status", "owns_house"]:
                X[col] = 0
            else:
                X[col] = "unknown"

    for col in ["age", "annual_income", "family_size"]:
        if col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")
            med = X[col].median()
            if pd.isna(med): med = 0
            X[col] = X[col].fillna(med)

    for col in ["disability_status", "owns_house"]:
        if col in X.columns:
            X[col] = X[col].fillna(0).astype(int)

    for col in ["gender", "education_level", "employment_status", "scheme_type"]:
        if col in X.columns:
            X[col] = X[col].fillna("unknown").astype(str)
            
    return X


class GovernmentUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        policy = request.data.get("policy", "scholarship")
        if not file:
            return Response({"error": "No file uploaded"}, status=400)
            
        try:
            df = pd.read_csv(file)
            service = GovernmentPredictionService()
            
            # Warn about missing columns based on policy rules
            available_cols = list(df.columns)
            conds = POLICY_CONDITIONS.get(policy, {})
            required_for_policy = list(conds.keys())
            missing = [c for c in required_for_policy if c not in available_cols]
            
            df = service.normalize(df)
            df = service.apply_aliases(df)
            
            X = prepare_model_input(df, policy, service.required_features)
            
            probs = service.model.predict_proba(X)[:, 1]
            df["eligibility_probability"] = probs
            df["eligible"] = (probs >= 0.5).astype(int)
            
            records = len(df)
            eligible = int(df["eligible"].sum())
            rejected = records - eligible
            rate = round(eligible / records, 4) if records > 0 else 0
            
            best_rule, best_rate = service.optimize_policy(df, policy)
            
            return Response({
                "status": "success",
                "data": json.loads(df.to_json(orient="records")),
                "metrics": {
                    "records_evaluated": records,
                    "eligible": eligible,
                    "rejected": rejected,
                    "eligibility_rate": rate
                },
                "optimized_recommendation": {
                    "rule": best_rule,
                    "rate": best_rate
                },
                "missing_cols": missing,
                "available_cols": available_cols
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class GovernmentFilterView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        policy = request.data.get("policy", "scholarship")
        filters = request.data.get("filters", {})
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df_pred = pd.DataFrame(data)
            service = GovernmentPredictionService()
            df_filtered = service.apply_policy_rules(df_pred, policy, filters)
            
            records = len(df_pred)
            if "eligible" in df_filtered.columns:
                eligible = int(df_filtered["eligible"].sum())
            else:
                eligible = len(df_filtered)
                
            rejected = records - eligible
            rate = round(eligible / records, 4) if records > 0 else 0
            
            best_rule, best_rate = service.optimize_policy(df_pred, policy)
            
            return Response({
                "status": "success",
                "filtered_data": json.loads(df_filtered.to_json(orient="records")),
                "metrics": {
                    "records_evaluated": records,
                    "eligible": eligible,
                    "rejected": rejected,
                    "eligibility_rate": rate
                },
                "optimized_recommendation": {
                    "rule": best_rule,
                    "rate": best_rate
                }
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class GovernmentExplainView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        filters = request.data.get("filters", {})
        policy = request.data.get("policy", "scholarship")
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df = pd.DataFrame(data)
            service = GovernmentPredictionService()
            
            df_filtered = service.apply_policy_rules(df, policy, filters)
            if len(df_filtered) == 0:
                return Response({"status": "success", "shap_data": []})
                
            # Limit data for SHAP to ensure performance
            df_shap = df_filtered.head(50)
            X = prepare_model_input(df_shap, policy, service.required_features)
            
            pipeline = service.model
            
            if hasattr(pipeline, "named_steps"):
                preprocessor = pipeline.named_steps.get("preprocessor")
                model_only = pipeline.named_steps.get("model")
                if not preprocessor or not model_only:
                    return Response({"error": "Model structure not compatible for SHAP"}, status=500)
                X_transformed = preprocessor.transform(X)
                feature_names = preprocessor.get_feature_names_out()
            else:
                model_only = pipeline
                X_transformed = X
                feature_names = X.columns
            
            # Convert sparse to dense if necessary
            if hasattr(X_transformed, "toarray"):
                X_transformed = X_transformed.toarray()
                
            explainer = shap.TreeExplainer(model_only)
            shap_values = explainer.shap_values(X_transformed)
            
            # Handle binary classifier output (list or 3rd dimension)
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
            return Response({"error": str(e)}, status=500)

class GovernmentGeminiSummaryView(APIView):
    def post(self, request):
        policy = request.data.get("policy", "scholarship")
        metrics = request.data.get("metrics", {})
        filters = request.data.get("filters", {})
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not found in environment"}, status=500)
            
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            model.generate_content("test")
        except Exception as e1:
            try:
                model = genai.GenerativeModel("gemini-pro")
                model.generate_content("test")
            except Exception as e2:
                return Response({"error": f"Gemini Error (1.5-flash): {str(e1)} | (Pro): {str(e2)}"}, status=500)
        
        prompt = f"""
You are an expert policy advisor analyzing {policy} policy data.

Current Policy Thresholds: {filters}
Current Impact Metrics: {metrics}

Provide a concise explanation (strictly addressing these three points):
1. Why the recommended policy threshold is optimal.
2. The estimated demographic reach (how many citizens will utilize it based on current metrics).
3. How this specific rule mitigates the risk of false claims or improper allocations.
"""
        
        try:
            response = model.generate_content(prompt)
            return Response({
                "status": "success",
                "explanation": response.text
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
