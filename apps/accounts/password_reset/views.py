from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.conf import settings
from datetime import timedelta
import logging

from .models import PasswordResetToken
from .serializers import PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from .services import send_password_reset_email

User = get_user_model()
logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Authentication'],
    summary='Request Password Reset',
    description='Request a password reset email. An email with reset link will be sent to the provided email address.',
    request=PasswordResetRequestSerializer,
    responses={
        200: {
            'description': 'Password reset email sent successfully',
            'examples': {
                'application/json': {
                    'message': 'Password reset email sent successfully',
                    'email': 'u***@example.com',
                }
            }
        },
        400: {'description': 'Validation error'},
        429: {'description': 'Rate limit exceeded'},
    },
    examples=[
        OpenApiExample(
            'Password Reset Request',
            value={
                'email': 'user@example.com',
            },
            request_only=True,
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', method='POST')
@ratelimit(key='post:email', rate='3/h', method='POST')
def password_reset_request(request):
    """
    Request password reset email.
    POST /api/v1/auth/password/reset/request/
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email'].lower().strip()
    
    # Find user by email (don't reveal if email exists)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if email exists for security
        return Response(
            {
                'message': 'If an account exists with this email, a password reset link has been sent.',
                'email': _mask_email(email)
            },
            status=status.HTTP_200_OK
        )
    
    # Generate reset token with transaction to ensure atomicity
    expires_at = timezone.now() + timedelta(minutes=getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY', 15))
    
    try:
        with transaction.atomic():
            # Invalidate any existing unused tokens for this user
            PasswordResetToken.objects.filter(
                user=user,
                is_used=False
            ).update(is_used=True)
            
            # Create new reset token
            reset_token = PasswordResetToken.objects.create(
                user=user,
                email=email,
                expires_at=expires_at
            )
            
            # Send reset email (if this fails, transaction will rollback)
            send_password_reset_email(user, reset_token.token)
            
    except Exception as e:
        # Log error but don't reveal it to user
        logger.error(f"Failed to process password reset request for {email}: {e}")
        return Response(
            {'error': 'Failed to send email. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response(
        {
            'message': 'Password reset email sent successfully',
            'email': _mask_email(email)
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Authentication'],
    summary='Confirm Password Reset',
    description='Reset password using token from email. Token expires after 15 minutes and can only be used once.',
    request=PasswordResetConfirmSerializer,
    responses={
        200: {
            'description': 'Password reset successfully',
            'examples': {
                'application/json': {
                    'message': 'Password reset successfully',
                }
            }
        },
        400: {'description': 'Invalid token or validation error'},
    },
    examples=[
        OpenApiExample(
            'Password Reset Confirm',
            value={
                'token': '550e8400-e29b-41d4-a716-446655440000',
                'password': 'newpassword123',
                'password_confirm': 'newpassword123',
            },
            request_only=True,
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')
def password_reset_confirm(request):
    """
    Confirm password reset with token.
    POST /api/v1/auth/password/reset/confirm/
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    password = serializer.validated_data['password']
    
    # Find token
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired reset token.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate token
    if not reset_token.is_valid():
        if reset_token.is_used:
            return Response(
                {'error': 'This reset token has already been used.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif reset_token.is_expired():
            return Response(
                {'error': 'Reset token has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Reset password with transaction
    try:
        with transaction.atomic():
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.mark_as_used()
    except Exception as e:
        logger.error(f"Failed to reset password for user {reset_token.user.email}: {e}")
        return Response(
            {'error': 'Failed to reset password. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response(
        {
            'message': 'Password reset successfully. You can now login with your new password.',
        },
        status=status.HTTP_200_OK
    )


def _mask_email(email):
    """Mask email for privacy (e.g., u***@example.com)"""
    if not email or '@' not in email:
        return email
    try:
        local, domain = email.split('@', 1)
        if len(local) <= 1:
            masked_local = '*'
        else:
            masked_local = local[0] + '*' * (len(local) - 1)
        return f"{masked_local}@{domain}"
    except Exception:
        return email
