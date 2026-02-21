from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/insurance/', include('insurance.urls')),
    path('api/government/', include('government.urls')),
    path('api/hr/', include('hr.urls')),
    path('api/', include('predictor.urls')),
]
