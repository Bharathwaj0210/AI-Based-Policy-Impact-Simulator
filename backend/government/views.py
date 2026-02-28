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
                "available_cols": list(df.columns)
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class GovernmentFilterView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        policy = request.data.get("policy", "scholarship")
        thresholds = request.data.get("thresholds", {})
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df_pred = pd.DataFrame(data)
            service = GovernmentPredictionService()
            df_filtered = service.apply_policy_rules(df_pred, policy, thresholds)
            
            records = len(df_filtered)
            eligible = int(df_filtered["eligible"].sum())
            rejected = records - eligible
            rate = round(eligible / records, 4) if records > 0 else 0
            
            return Response({
                "status": "success",
                "filtered_data": json.loads(df_filtered.to_json(orient="records")),
                "metrics": {
                    "records_evaluated": records,
                    "eligible": eligible,
                    "rejected": rejected,
                    "eligibility_rate": rate
                }
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class GovernmentExplainView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        policy = request.data.get("policy", "scholarship")
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df = pd.DataFrame(data)
            service = GovernmentPredictionService()
            X = prepare_model_input(df, policy, service.required_features)
            
            pipeline = service.model
            preprocessor = pipeline.named_steps.get("preprocessor")
            model_only = pipeline.named_steps.get("model")
            
            if not preprocessor or not model_only:
                return Response({"error": "Model structure not compatible for SHAP"}, status=500)
                
            X_transformed = preprocessor.transform(X)
            explainer = shap.TreeExplainer(model_only)
            shap_values = explainer.shap_values(X_transformed)
            sv = shap_values[1] if isinstance(shap_values, list) else shap_values
            
            feature_names = preprocessor.get_feature_names_out()
            n_features = min(len(feature_names), sv.shape[1])
            feature_names = feature_names[:n_features]
            sv_slice = sv[:, :n_features]
            
            shap_importance = np.abs(sv_slice).mean(axis=0)
            
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

class GovernmentGeminiSummaryView(APIView):
    def post(self, request):
        policy = request.data.get("policy", "scholarship")
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not found in environment"}, status=500)
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = f"""
        Risk scores and eligibility are generated by trained machine learning models for the {policy} government policy.
        Policy conditions and rules act as filters on top of these model predictions to ensure citizens meet thresholds.
        Please provide a short business-friendly explanation summarizing this AI-driven eligibility process.
        """
        
        try:
            response = model.generate_content(prompt)
            return Response({
                "status": "success",
                "explanation": response.text
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)
