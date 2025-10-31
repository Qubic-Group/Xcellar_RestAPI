from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting password reset"""
    email = serializers.EmailField(
        required=True,
        help_text='Email address associated with your account'
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset"""
    token = serializers.UUIDField(
        required=True,
        help_text='Password reset token from email'
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        validators=[validate_password],
        help_text='New password (minimum 8 characters)'
    )
    password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        help_text='Confirm new password'
    )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

