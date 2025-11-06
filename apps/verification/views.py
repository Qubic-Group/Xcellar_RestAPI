from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.conf import settings

from .models import PhoneVerification
from .serializers import SendOTPSerializer, VerifyOTPSerializer
from .utils import get_otp_expiry_time
from .services import twilio_service


@extend_schema(
    tags=['Verification'],
    summary='Send OTP',
    description='Send OTP code to phone number via SMS, WhatsApp, or Voice Call. Rate limited to prevent abuse.',
    request=SendOTPSerializer,
    responses={
        200: {
            'description': 'OTP sent successfully',
            'examples': {
                'application/json': {
                    'message': 'OTP sent successfully',
                    'expires_in': 300,
                    'method': 'SMS',
                }
            }
        },
        400: {'description': 'Validation error - check request body'},
        429: {'description': 'Rate limit exceeded'},
    },
    examples=[
        OpenApiExample(
            'Send OTP Request',
            value={
                'phone_number': '+1234567890',
                'method': 'SMS',
            },
            request_only=True,
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/h', method='POST')
def send_otp(request):
    """
    Send OTP code to phone number using Twilio Verify API.
    POST /api/v1/verification/send/
    """
    serializer = SendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    method = serializer.validated_data['method']
    
    # Check cooldown period (prevent spam)
    cooldown_seconds = getattr(settings, 'OTP_COOLDOWN_SECONDS', 60)
    recent_verification = PhoneVerification.objects.filter(
        phone_number=phone_number,
        created_at__gte=timezone.now() - timezone.timedelta(seconds=cooldown_seconds)
    ).first()
    
    if recent_verification:
        remaining = cooldown_seconds - int((timezone.now() - recent_verification.created_at).total_seconds())
        return Response(
            {
                'error': f'Please wait {remaining} seconds before requesting another OTP',
                'cooldown_remaining': remaining
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    expires_at = get_otp_expiry_time()
    
    # Invalidate any existing unverified OTPs for this phone number
    PhoneVerification.objects.filter(
        phone_number=phone_number,
        is_verified=False
    ).update(is_active=False)
    
    # Send OTP via Twilio Verify API (Twilio generates the code)
    success, message, verification_sid = twilio_service.send_otp(phone_number, method)
    
    if not success:
        return Response(
            {'error': message},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Create verification record for tracking (Twilio handles the actual code)
    PhoneVerification.objects.create(
        phone_number=phone_number,
        code_hash=verification_sid or '',  # Store Twilio verification SID for reference
        verification_method=method,
        expires_at=expires_at,
    )
    
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
    return Response(
        {
            'message': 'OTP sent successfully',
            'expires_in': expiry_minutes * 60,
            'method': method,
        },
        status=status.HTTP_200_OK
    )


@extend_schema(
    tags=['Verification'],
    summary='Verify OTP',
    description='Verify OTP code sent to phone number. Code expires after 5 minutes.',
    request=VerifyOTPSerializer,
    responses={
        200: {
            'description': 'OTP verified successfully',
            'examples': {
                'application/json': {
                    'verified': True,
                    'message': 'Phone number verified successfully',
                }
            }
        },
        400: {'description': 'Invalid OTP code or validation error'},
        429: {'description': 'Too many verification attempts'},
    },
    examples=[
        OpenApiExample(
            'Verify OTP Request',
            value={
                'phone_number': '+1234567890',
                'code': '123456',
            },
            request_only=True,
        ),
    ],
)
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='20/h', method='POST')
def verify_otp(request):
    """
    Verify OTP code using Twilio Verify API.
    POST /api/v1/verification/verify/
    """
    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']
    
    # Find the latest unverified, unexpired OTP for this phone number
    verification = PhoneVerification.objects.filter(
        phone_number=phone_number,
        is_verified=False,
        is_active=True
    ).order_by('-created_at').first()
    
    if not verification:
        return Response(
            {'error': 'No active verification code found. Please request a new verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if expired
    if verification.is_expired():
        return Response(
            {'error': 'Verification code has expired. Please request a new verification code.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check attempts
    if not verification.can_attempt():
        if verification.attempts >= verification.max_attempts:
            return Response(
                {'error': 'Too many verification attempts. Please request a new verification code and try again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
    
    # Verify code using Twilio Verify API
    success, message = twilio_service.verify_otp(phone_number, code)
    
    if success:
        verification.mark_verified()
        return Response(
            {
                'verified': True,
                'message': 'Phone number verified successfully',
            },
            status=status.HTTP_200_OK
        )
    else:
        verification.increment_attempts()
        remaining_attempts = verification.max_attempts - verification.attempts
        return Response(
            {
                'error': message,
                'remaining_attempts': remaining_attempts,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

