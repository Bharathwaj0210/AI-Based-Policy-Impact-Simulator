import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from insurance.services import predict_insurance
from hr.services import predict_hr
from core.ai_services import GeminiAIService

class PredictionView(APIView):
    parser_classes = [MultiPartParser]

    @csrf_exempt
    def post(self, request, insurance_type):
        """
        Accepts a POST request with a CSV file and calls the appropriate prediction service.
        """
        # Determine if it's an HR or Insurance policy
        hr_types = ['attrition', 'recruitment']
        
        if 'file' not in request.FILES:
            return JsonResponse({
                "status": "error",
                "message": "Missing file"
            }, status=400)

        file = request.FILES['file']
        
        try:
            # Read CSV using pandas
            df = pd.read_csv(file)
        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Invalid CSV: {str(e)}"
            }, status=400)

        # Route to the correct service
        if insurance_type.lower() in hr_types:
            result = predict_hr(df, insurance_type)
        else:
            result = predict_insurance(df, insurance_type)

        if result.get('status') == 'error':
            return JsonResponse(result, status=500)

        return JsonResponse(result)

class ExplanationView(APIView):
    """
    API View to provide AI-generated explanations for predictions.
    """
    def post(self, request, insurance_type):
        data = request.data
        prediction_results = data.get("predictions")
        data_summary = data.get("summary")

        if not prediction_results:
            return JsonResponse({"status": "error", "message": "Missing prediction results"}, status=400)

        ai_service = GeminiAIService()
        explanation = ai_service.explain_prediction(insurance_type, data_summary, prediction_results)

        return JsonResponse({
            "status": "success",
            "policy_type": insurance_type,
            "explanation": explanation
        })
