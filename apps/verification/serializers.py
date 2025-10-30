from rest_framework import serializers
from django.core.validators import RegexValidator
from django.utils import timezone
from .models import PhoneVerification
from .utils import generate_otp_code, hash_otp_code, get_otp_expiry_time
from .services import twilio_service


class SendOTPSerializer(serializers.Serializer):
    """Serializer for sending OTP"""
    phone_number = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text='Phone number in international format (e.g., +1234567890)'
    )
    method = serializers.ChoiceField(
        choices=PhoneVerification.VERIFICATION_METHOD_CHOICES,
        default='SMS',
        help_text='Verification method: SMS, WhatsApp, or Voice Call'
    )
    
    def validate_phone_number(self, value):
        """Normalize phone number format"""
        # Ensure phone number starts with +
        if not value.startswith('+'):
            value = '+' + value.lstrip('+')
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Serializer for verifying OTP"""
    phone_number = serializers.CharField(
        required=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text='Phone number in international format (e.g., +1234567890)'
    )
    code = serializers.CharField(
        required=True,
        min_length=4,
        max_length=10,
        help_text='OTP code received via SMS/WhatsApp/Voice'
    )
    
    def validate_phone_number(self, value):
        """Normalize phone number format"""
        if not value.startswith('+'):
            value = '+' + value.lstrip('+')
        return value

