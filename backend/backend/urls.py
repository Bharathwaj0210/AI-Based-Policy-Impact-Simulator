from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home_view(request):
    return JsonResponse({"message": "Welcome to the AI Policy Simulator Backend API. Access /api/<domain>/ for specific endpoints."})

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('api/insurance/', include('insurance.urls')),
    path('api/government/', include('government.urls')),
    path('api/hr/', include('hr.urls')),
    path('api/', include('predictor.urls')),
]
