from django.urls import path
from .views import (
    GovernmentUploadView,
    GovernmentFilterView,
    GovernmentExplainView,
    GovernmentGeminiSummaryView
)

urlpatterns = [
    path('upload/', GovernmentUploadView.as_view(), name='government-upload'),
    path('filter/', GovernmentFilterView.as_view(), name='government-filter'),
    path('explain/', GovernmentExplainView.as_view(), name='government-explain'),
    path('gemini-summary/', GovernmentGeminiSummaryView.as_view(), name='government-gemini'),
]
