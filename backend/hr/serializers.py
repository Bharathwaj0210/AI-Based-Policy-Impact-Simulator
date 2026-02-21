from rest_framework import serializers
from .models import HRPolicy

class HRPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = HRPolicy
        fields = '__all__'
