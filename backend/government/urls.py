from django.urls import path
from .views import GovernmentPredictionView, GovernmentOptimizationView

urlpatterns = [
    path('predict/<str:policy>/', GovernmentPredictionView.as_view(), name='government-predict'),
    path('optimize/<str:policy>/', GovernmentOptimizationView.as_view(), name='government-optimize'),
]
