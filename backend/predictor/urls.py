from django.urls import path
from .views import PredictionView, ExplanationView

urlpatterns = [
    path('predict/<str:insurance_type>/', PredictionView.as_view(), name='predict_insurance'),
    path('explain/<str:insurance_type>/', ExplanationView.as_view(), name='explain_policy'),
]
