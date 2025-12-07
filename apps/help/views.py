from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.core.response import success_response, error_response, created_response, validation_error_response
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiExample
import logging

from .models import HelpRequest
from .serializers import HelpRequestSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Help'],
    summary='Submit Help Request',
    description='Submit a help/support request. The request will be saved to the database. If authenticated, user information will be auto-filled.',
    request=HelpRequestSerializer,
    responses={
        201: {
            'description': 'Help request submitted successfully',
            'examples': {
                'application/json': {
                    'message': 'Help request submitted successfully',
                    'request_id': 1,
                    'status': 'PENDING',
                }
            }
        },
        400: {'description': 'Validation error'},
        429: {'description': 'Rate limit exceeded'},
    },
    examples=[
        OpenApiExample(
            'Submit Help Request (Authenticated)',
            value={
                'subject': 'Payment Issue',
                'message': 'I am having trouble processing my payment. The transaction keeps failing.',
                'category': 'PAYMENT',
                'priority': 'HIGH',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Submit Help Request (Anonymous)',
            value={
                'user_email': 'user@example.com',
                'user_name': 'John Doe',
                'phone_number': '+1234567890',
                'subject': 'Account Problem',
                'message': 'I cannot log into my account. Please help.',
                'category': 'ACCOUNT',
                'priority': 'NORMAL',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Help Request Response',
            value={
                'message': 'Help request submitted successfully',
                'request_id': 1,
                'status': 'PENDING',
            },
            response_only=True,
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])  # Allow both authenticated and anonymous users
@ratelimit(key='ip', rate='5/h', method='POST')  # Limit to 5 requests per hour per IP
def submit_help_request(request):
    """
    Submit a help/support request.
    POST /api/v1/help/request/
    
    If user is authenticated, user information will be auto-filled.
    """
    serializer = HelpRequestSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return validation_error_response(serializer.errors, message='Validation error')
    
    try:
        with transaction.atomic():
            # Create help request
            help_request = serializer.save()
        
        return created_response(
            data={'request_id': help_request.id, 'status': help_request.status},
            message='Help request submitted successfully'
        )
    except Exception as e:
        logger.error(f"Error creating help request: {e}")
        return error_response('Unable to submit help request at this time. Please try again later or contact support directly.', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Help'],
    summary='Get My Help Requests',
    description='Retrieve help requests submitted by the authenticated user. Requires authentication.',
    responses={
        200: {
            'description': 'List of user\'s help requests',
            'examples': {
                'application/json': {
                    'requests': [
                        {
                            'id': 1,
                            'subject': 'Payment Issue',
                            'status': 'PENDING',
                            'category': 'PAYMENT',
                            'created_at': '2025-10-30T18:00:00Z',
                        }
                    ]
                }
            }
        },
        401: {'description': 'Authentication required'},
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/h', method='GET')
def my_help_requests(request):
    """
    Get help requests submitted by the authenticated user.
    GET /api/v1/help/my-requests/
    """
    help_requests = HelpRequest.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    return success_response(
        data={
            'requests': [
                {
                    'id': req.id,
                    'subject': req.subject,
                    'message': req.message[:200] + '...' if len(req.message) > 200 else req.message,
                    'category': req.category,
                    'category_display': req.get_category_display(),
                    'priority': req.priority,
                    'priority_display': req.get_priority_display(),
                    'status': req.status,
                    'status_display': req.get_status_display(),
                    'created_at': req.created_at.isoformat(),
                    'updated_at': req.updated_at.isoformat(),
                }
                for req in help_requests
            ],
            'count': help_requests.count(),
        },
        message='Help requests retrieved successfully'
    )

