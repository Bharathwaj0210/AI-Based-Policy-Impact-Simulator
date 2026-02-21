from rest_framework import serializers
from .models import GovernmentPolicy

class GovernmentPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentPolicy
        fields = '__all__'
