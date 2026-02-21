from rest_framework.views import APIView
from rest_framework.response import Response
from .models import InsurancePolicy
from .serializers import InsurancePolicySerializer

class InsurancePolicyListView(APIView):
    def get(self, request):
        policies = InsurancePolicy.objects.all()
        serializer = InsurancePolicySerializer(policies, many=True)
        return Response(serializer.data)
