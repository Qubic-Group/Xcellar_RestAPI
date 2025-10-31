from django.db import models
from django.conf import settings
from apps.core.models import AbstractBaseModel


def validate_document_file(value):
    """Validate document file types (PDF, images, DOC)"""
    import os
    ext = os.path.splitext(value.name)[1].lower()
    allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    if ext not in allowed_extensions:
        from django.core.exceptions import ValidationError
        raise ValidationError(
            f'File type not allowed. Allowed types: PDF, DOC, DOCX, JPG, JPEG, PNG, GIF, BMP, WEBP'
        )


class Vehicle(AbstractBaseModel):
    """
    Vehicle model for couriers.
    Only couriers can register and manage vehicles.
    """
    OWNERSHIP_CHOICES = [
        ('OWNED', 'Owned'),
        ('COMPANY', 'Company'),
        ('LEASED', 'Leased'),
    ]
    
    VEHICLE_TYPE_CHOICES = [
        ('MOTORCYCLE', 'Motorcycle'),
        ('CAR', 'Car'),
        ('VAN', 'Van'),
        ('TRUCK', 'Truck'),
        ('BICYCLE', 'Bicycle'),
    ]
    
    # Relationships
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vehicles',
        limit_choices_to={'user_type': 'COURIER'}
    )
    
    # Vehicle Information
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    ownership_condition = models.CharField(max_length=10, choices=OWNERSHIP_CHOICES)
    manufacturer = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year_of_manufacturing = models.IntegerField()
    license_plate_number = models.CharField(max_length=20, unique=True)
    
    # Document Uploads (Optional - can be added during update)
    registration_proof = models.FileField(
        upload_to='vehicles/documents/registration/',
        blank=True,
        null=True,
        validators=[validate_document_file],
        help_text='Upload registration proof document (PDF, DOC, DOCX, or Image)'
    )
    insurance_policy_proof = models.FileField(
        upload_to='vehicles/documents/insurance/',
        blank=True,
        null=True,
        validators=[validate_document_file],
        help_text='Upload insurance policy proof document (PDF, DOC, DOCX, or Image)'
    )
    road_worthiness_proof = models.FileField(
        upload_to='vehicles/documents/roadworthiness/',
        blank=True,
        null=True,
        validators=[validate_document_file],
        help_text='Upload road worthiness proof document (PDF, DOC, DOCX, or Image)'
    )
    
    class Meta:
        db_table = 'vehicles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['courier', 'is_active']),
            models.Index(fields=['license_plate_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['license_plate_number'],
                name='unique_license_plate'
            )
        ]
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
    
    def __str__(self):
        return f"{self.manufacturer} {self.model} - {self.license_plate_number}"


class DriverLicense(AbstractBaseModel):
    """
    Driver's License model for couriers.
    One license per courier (OneToOne relationship).
    """
    courier_profile = models.OneToOneField(
        'accounts.CourierProfile',
        on_delete=models.CASCADE,
        related_name='driver_license'
    )
    
    # License Information (Optional)
    license_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Driver license number'
    )
    issue_date = models.DateField(
        blank=True,
        null=True,
        help_text='Date when license was issued'
    )
    expiry_date = models.DateField(
        blank=True,
        null=True,
        help_text='Date when license expires'
    )
    issuing_authority = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Authority that issued the license (e.g., DMV, Transport Authority)'
    )
    
    # Document Uploads (Optional)
    front_page = models.FileField(
        upload_to='licenses/documents/front/',
        blank=True,
        null=True,
        validators=[validate_document_file],
        help_text='Driver license front page (PDF, DOC, DOCX, or Image)'
    )
    back_page = models.FileField(
        upload_to='licenses/documents/back/',
        blank=True,
        null=True,
        validators=[validate_document_file],
        help_text='Driver license back page (PDF, DOC, DOCX, or Image)'
    )
    
    class Meta:
        db_table = 'driver_licenses'
        verbose_name = 'Driver License'
        verbose_name_plural = 'Driver Licenses'
    
    def __str__(self):
        if self.license_number:
            return f"{self.courier_profile.full_name} - {self.license_number}"
        return f"{self.courier_profile.full_name} - Driver License"
    
    def is_expired(self):
        """Check if license has expired"""
        if self.expiry_date:
            from django.utils import timezone
            return timezone.now().date() > self.expiry_date
        return None  # Unknown if no expiry date
