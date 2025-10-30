from django.urls import path
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.decorators import ratelimit

from apps.core.permissions import IsUser


@api_view(['GET'])
@permission_classes([IsUser])
@ratelimit(key='user', rate='100/h', method='GET')
def user_dashboard(request):
    """
    User dashboard endpoint.
    GET /api/v1/users/dashboard/
    """
    return Response({
        'message': 'User dashboard',
        'user': request.user.email
    }, status=status.HTTP_200_OK)


app_name = 'users'

urlpatterns = [
    path('dashboard/', user_dashboard, name='user_dashboard'),
]

