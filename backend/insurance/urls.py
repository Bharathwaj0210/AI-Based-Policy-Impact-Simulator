from django.urls import path
from .views import InsurancePolicyListView

urlpatterns = [
    path('policies/', InsurancePolicyListView.as_view(), name='policy-list'),
]
