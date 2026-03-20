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
from .models import HRPolicy
from .serializers import HRPolicySerializer
from .services import HRPredictionService

REQUIRED_FEATURES = [
    "age",
    "tenureyears",
    "performance score",
    "current employee rating",
    "isactive"
]

def suggest_policy(df, score_col, user_filters=None):
    if df.empty or score_col not in df.columns:
        return None
    user_filters = user_filters or {}
    base_score = df[score_col].mean()
    best_score = base_score
    best_rule = None

    for age in [18, 22, 25, 30]:
        for rating in [2, 3, 4]:
            for tenure in [0, 1, 3]:
                temp = df[
                    (df["age"] >= age) &
                    (df["current employee rating"] >= rating) &
                    (df["tenureyears"] >= tenure)
                ]
                if len(temp) < 10:
                    continue
                score = temp[score_col].mean()
                if score < best_score - 0.01:
                    best_score = score
                    best_rule = {
                        "Minimum Age": age,
                        "Minimum Rating": rating,
                        "Minimum Tenure": tenure
                    }
    user_rule = {
        "Minimum Age": user_filters.get("age_min", 18),
        "Minimum Rating": user_filters.get("rating_min", 1),
        "Minimum Tenure": user_filters.get("tenure_min", 0)
    }
    if best_rule is None:
        return None
    return best_rule

class HRUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        policy_option = request.data.get("policy_option", "Recruitment")  # Recruitment or Attrition
        if not file:
            return Response({"error": "No file uploaded"}, status=400)
            
        try:
            df_original = pd.read_csv(file)
            df_original.columns = df_original.columns.str.strip().str.lower()
            
            for col in REQUIRED_FEATURES:
                if col not in df_original.columns:
                    df_original[col] = np.random.randint(1, 5, len(df_original))
                df_original[col] = pd.to_numeric(df_original[col], errors="coerce")
                df_original[col] = df_original[col].fillna(df_original[col].median())
                
            service = HRPredictionService(hr_type=policy_option.lower())
            
            X = df_original[REQUIRED_FEATURES]
            
            if hasattr(service.model, "predict_proba"):
                risk_scores = service.model.predict_proba(X)[:, 1]
            else:
                risk_scores = service.model.predict(X)
                
            score_col = f"{policy_option}_Risk_Score"
            df_original[score_col] = risk_scores
            
            df_sorted = df_original.sort_values(score_col)
            n = len(df_sorted)
            if n > 0:
                best_df = df_sorted.iloc[:int(0.3*n)]
                avg_df = df_sorted.iloc[int(0.3*n):int(0.7*n)]
                worst_df = df_sorted.iloc[int(0.7*n):]
                
                df_sorted.loc[best_df.index, 'case_type'] = 'Best Case'
                df_sorted.loc[avg_df.index, 'case_type'] = 'Average Case'
                df_sorted.loc[worst_df.index, 'case_type'] = 'Worst Case'
            else:
                df_sorted['case_type'] = 'Unknown'
            
            summary_stats = df_sorted.groupby("case_type").agg(
                Records=(score_col, "count"),
                Avg_Risk=(score_col, "mean")
            ).reset_index().to_dict('records')
            
            recommendation = suggest_policy(df_sorted, score_col, {})
            
            return Response({
                "status": "success",
                "data": json.loads(df_sorted.to_json(orient='records')),
                "summary": summary_stats,
                "score_col": score_col,
                "suggested_policy": recommendation
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class HRFilterView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        filters = request.data.get("filters", {})
        score_col = request.data.get("score_col", "Recruitment_Risk_Score")
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        df = pd.DataFrame(data)
        
        age_min = filters.get("age_min", 18)
        rating_min = filters.get("rating_min", 1)
        tenure_min = filters.get("tenure_min", 0)
        
        filtered_df = df[
            (df["age"] >= age_min) &
            (df["current employee rating"] >= rating_min) &
            (df["tenureyears"] >= tenure_min)
        ].copy()
        
        
        recommendation = suggest_policy(df, score_col, filters)
        
        return Response({
            "status": "success",
            "eligible_count": len(filtered_df),
            "rejected_count": len(df) - len(filtered_df),
            "total_count": len(df),
            "recommendation": recommendation
        })

class HRExplainView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        filters = request.data.get("filters", {})
        policy_option = request.data.get("policy_option", "Recruitment")
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df = pd.DataFrame(data)
            
            age_min = filters.get("age_min", 18)
            rating_min = filters.get("rating_min", 1)
            tenure_min = filters.get("tenure_min", 0)
            
            df_filtered = df[
                (df["age"] >= age_min) &
                (df["current employee rating"] >= rating_min) &
                (df["tenureyears"] >= tenure_min)
            ].copy()
            
            # Limit data for SHAP to ensure performance
            df_shap = df_filtered.head(50)
            X = df_shap[REQUIRED_FEATURES]
            service = HRPredictionService(hr_type=policy_option.lower())
            
            pipeline = service.model
            if hasattr(pipeline, "named_steps"):
                preprocessor = pipeline.named_steps.get("preprocessor")
                model = pipeline.named_steps.get("model")
                if preprocessor:
                    X_transformed = preprocessor.transform(X)
                else:
                    X_transformed = X
            else:
                model = pipeline
                preprocessor = None
                X_transformed = X
                
            # Convert sparse to dense if necessary
            if hasattr(X_transformed, "toarray"):
                X_transformed = X_transformed.toarray()

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_transformed)
            
            # Handle binary classifier output (list or 3rd dimension)
            if isinstance(shap_values, list):
                sv = shap_values[1] if len(shap_values) > 1 else shap_values[0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                sv = shap_values[:, :, 1] if shap_values.shape[2] > 1 else shap_values[:, :, 0]
            else:
                sv = shap_values
                
            if preprocessor:
                feature_names = preprocessor.get_feature_names_out()
            else:
                feature_names = REQUIRED_FEATURES
                
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

class HRGeminiSummaryView(APIView):
    def post(self, request):
        policy_option = request.data.get("policy_option", "Recruitment")
        scenario = request.data.get("scenario", "Average Case")
        summary_data = request.data.get("summary_data", {})
        filters = request.data.get("filters", {})
        metrics = request.data.get("metrics", {})
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not found in environment"}, status=500)
            
        genai.configure(api_key=api_key)
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""
You are an HR analytics expert analyzing scenarios for the {policy_option} policy.

Current Policy Thresholds: {filters}
Current Impact Metrics: {metrics}
Dataset summary: {summary_data}

INSTRUCTIONS:
Provide a detailed and granular comparison of three performance scenarios: Best Case, Average Case, and Worst Case.
You MUST return the data in a strict JSON format with the following structure:
{{
  "scenarios": [
    {{
      "scenario": "Best Case",
      "strategic_focus": "Short focus point (10-15 words)",
      "client_impact": "Short impact point (10-15 words)",
      "risk_control": "Short control point (10-15 words)"
    }},
    {{
      "scenario": "Average Case",
      "strategic_focus": "...",
      "client_impact": "...",
      "risk_control": "..."
    }},
    {{
      "scenario": "Worst Case",
      "strategic_focus": "...",
      "client_impact": "...",
      "risk_control": "..."
    }}
  ],
  "overall_summary": "A concise 2-sentence summary of the policy's estimated workforce impact and risk reduction mechanism."
}}
"""
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            try:
                result = json.loads(response.text)
                return Response({
                    "status": "success",
                    "scenarios": result.get("scenarios", []),
                    "overall_summary": result.get("overall_summary", "")
                })
            except Exception as json_err:
                print(f"JSON Parse Error in HR Gemini: {json_err}")
                return Response({
                    "status": "success",
                    "explanation": response.text  # Fallback
                })
        except Exception as e:
            import traceback
            print("ERROR IN HRGeminiSummaryView:")
            traceback.print_exc()
            return Response({"error": f"Gemini Error: {str(e)}"}, status=500)

class HRPolicyListView(APIView):
    def get(self, request):
        policies = HRPolicy.objects.all()
        serializer = HRPolicySerializer(policies, many=True)
        return Response(serializer.data)
