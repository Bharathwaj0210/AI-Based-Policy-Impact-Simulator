from django.urls import path
from .views import HRPolicyListView

urlpatterns = [
    path('policies/', HRPolicyListView.as_view(), name='hr-policy-list'),
]
