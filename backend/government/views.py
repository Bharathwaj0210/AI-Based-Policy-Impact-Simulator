import pandas as pd
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from .services import GovernmentPredictionService

class GovernmentPredictionView(APIView):
    parser_classes = [MultiPartParser]
    def post(self, request, policy):
        file = request.FILES.get('file')
        if not file: return Response({"status": "error", "message": "Missing file"}, status=400)
        try:
            df = pd.read_csv(file)
            service = GovernmentPredictionService()
            result = service.predict(df)
            if result['status'] == 'error': return Response(result, status=500)
            
            df_pred = pd.DataFrame(result['predictions'], columns=['eligible'])
            # Add other columns from df for rule application if needed, but service.predict returns used_features
            # For simplicity, we assume result has what we need or we re-merge
            # Actually service.predict returns a list of predictions.
            # Let's refine the service and view to be more cohesive.
            return Response(result)
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=400)

class GovernmentOptimizationView(APIView):
    def post(self, request, policy):
        data = request.data
        predictions = data.get("predictions")
        if not predictions: return Response({"status": "error", "message": "Missing predictions"}, status=400)
        df_pred = pd.DataFrame(predictions)
        service = GovernmentPredictionService()
        rule, rate = service.optimize_policy(df_pred, policy)
        return Response({"status": "success", "best_rule": rule, "best_rate": rate})
