from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from apps.core.models import AbstractBaseModel


class PhoneVerification(AbstractBaseModel):
    """
    Model to store phone verification OTP codes.
    """
    VERIFICATION_METHOD_CHOICES = [
        ('SMS', 'SMS'),
        ('WHATSAPP', 'WhatsApp'),
        ('VOICE', 'Voice Call'),
    ]

    phone_number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        db_index=True
    )
    code_hash = models.CharField(max_length=255)  # Hashed OTP code
    verification_method = models.CharField(
        max_length=10,
        choices=VERIFICATION_METHOD_CHOICES,
        default='SMS'
    )
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'phone_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'created_at']),
            models.Index(fields=['phone_number', 'is_verified']),
        ]
        verbose_name = 'Phone Verification'
        verbose_name_plural = 'Phone Verifications'

    def __str__(self):
        return f"{self.phone_number} - {self.verification_method}"

    def is_expired(self):
        """Check if verification code has expired"""
        return timezone.now() > self.expires_at

    def can_attempt(self):
        """Check if more verification attempts are allowed"""
        return self.attempts < self.max_attempts and not self.is_expired() and not self.is_verified

    def mark_verified(self):
        """Mark verification as successful"""
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=['is_verified', 'verified_at'])

    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])

