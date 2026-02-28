from django.urls import path
from .views import (
    HRPolicyListView,
    HRUploadView,
    HRFilterView,
    HRExplainView,
    HRGeminiSummaryView
)

urlpatterns = [
    path('policies/', HRPolicyListView.as_view(), name='hr-policy-list'),
    path('upload/', HRUploadView.as_view(), name='hr-upload'),
    path('filter/', HRFilterView.as_view(), name='hr-filter'),
    path('explain/', HRExplainView.as_view(), name='hr-explain'),
    path('gemini-summary/', HRGeminiSummaryView.as_view(), name='hr-gemini'),
]
