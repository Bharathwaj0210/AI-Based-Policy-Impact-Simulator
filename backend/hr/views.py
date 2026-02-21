from rest_framework.views import APIView
from rest_framework.response import Response
from .models import HRPolicy
from .serializers import HRPolicySerializer

class HRPolicyListView(APIView):
    def get(self, request):
        policies = HRPolicy.objects.all()
        serializer = HRPolicySerializer(policies, many=True)
        return Response(serializer.data)
