from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.decorators import ratelimit

from apps.core.permissions import IsCourier


@api_view(['GET'])
@permission_classes([IsCourier])
@ratelimit(key='user', rate='100/h', method='GET')
def courier_dashboard(request):
    """
    Courier dashboard endpoint.
    GET /api/v1/couriers/dashboard/
    """
    return Response({
        'message': 'Courier dashboard',
        'courier': request.user.email
    }, status=status.HTTP_200_OK)


app_name = 'couriers'

urlpatterns = [
    path('dashboard/', courier_dashboard, name='courier_dashboard'),
]

