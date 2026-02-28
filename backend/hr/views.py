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
            
            return Response({
                "status": "success",
                "data": json.loads(df_sorted.to_json(orient='records')),
                "summary": summary_stats,
                "score_col": score_col
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
        
        # Recommendation Logic
        def suggest_policy(df, score_col, user_filters):
            if df.empty or score_col not in df.columns:
                return None
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
                "Minimum Age": user_filters.get("age_min"),
                "Minimum Rating": user_filters.get("rating_min"),
                "Minimum Tenure": user_filters.get("tenure_min")
            }
            if best_rule is None or best_rule == user_rule:
                return None
            return best_rule
            
        recommendation = suggest_policy(df, score_col, filters)
        
        return Response({
            "status": "success",
            "eligible_count": len(filtered_df),
            "rejected_count": len(df) - len(filtered_df),
            "total_count": len(df),
            "recommendation": recommendation if recommendation else "Current policy is already optimal."
        })

class HRExplainView(APIView):
    def post(self, request):
        data = request.data.get("data", [])
        policy_option = request.data.get("policy_option", "Recruitment")
        
        if not data:
            return Response({"error": "No data provided"}, status=400)
            
        try:
            df = pd.DataFrame(data)
            X = df[REQUIRED_FEATURES]
            service = HRPredictionService(hr_type=policy_option.lower())
            explainer = shap.TreeExplainer(service.model)
            shap_values = explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
                
            shap_importance = np.abs(shap_values).mean(axis=0)
            
            shap_table = pd.DataFrame({
                "Feature": REQUIRED_FEATURES,
                "Mean_SHAP_Impact": shap_importance,
                "Impact_%": 100 * shap_importance / shap_importance.sum()
            }).sort_values("Impact_%", ascending=False).to_dict('records')
            
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
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return Response({"error": "GEMINI_API_KEY not found in environment"}, status=500)
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-flash-latest")
        
        prompt = f"""
        You are an HR analytics expert.

        Explain the {scenario} scenario for {policy_option} policy.

        Dataset summary:
        {summary_data}

        Give 3 short bullet points:
        - Risk interpretation
        - HR implication
        - Action suggestion
        """
        
        try:
            response = model.generate_content(prompt)
            return Response({
                "status": "success",
                "explanation": response.text
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class HRPolicyListView(APIView):
    def get(self, request):
        policies = HRPolicy.objects.all()
        serializer = HRPolicySerializer(policies, many=True)
        return Response(serializer.data)
