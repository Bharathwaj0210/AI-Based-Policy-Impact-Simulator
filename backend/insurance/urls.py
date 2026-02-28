from django.urls import path
from .views import (
    InsurancePolicyListView, 
    InsuranceUploadView, 
    InsuranceFilterView, 
    InsuranceExplainView, 
    InsuranceGeminiSummaryView
)

urlpatterns = [
    path('policies/', InsurancePolicyListView.as_view(), name='policy-list'),
    path('upload/', InsuranceUploadView.as_view(), name='insurance-upload'),
    path('filter/', InsuranceFilterView.as_view(), name='insurance-filter'),
    path('explain/', InsuranceExplainView.as_view(), name='insurance-explain'),
    path('gemini-summary/', InsuranceGeminiSummaryView.as_view(), name='insurance-gemini'),
]
