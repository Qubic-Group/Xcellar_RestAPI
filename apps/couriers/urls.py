from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import VehicleViewSet, driver_license, update_driver_license, courier_dashboard

# Create router and register viewsets
router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')

app_name = 'couriers'

# Combine router URLs with function-based views
urlpatterns = [
    path('dashboard/', courier_dashboard, name='courier_dashboard'),
    path('license/', driver_license, name='driver_license'),
    path('license/update/', update_driver_license, name='update_driver_license'),
    path('', include(router.urls)),
]
