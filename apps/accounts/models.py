from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

from apps.core.models import AbstractBaseModel


class UserManager(BaseUserManager):
    """Custom user manager"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with user_type differentiation.
    """
    USER_TYPE_CHOICES = [
        ('USER', 'Regular Customer'),
        ('COURIER', 'Courier/Driver'),
    ]

    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ]
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        if self.user_type == 'USER' and hasattr(self, 'user_profile'):
            return f"{self.user_profile.first_name} {self.user_profile.last_name}"
        elif self.user_type == 'COURIER' and hasattr(self, 'courier_profile'):
            return f"{self.courier_profile.first_name} {self.courier_profile.last_name}"
        return self.email

    def get_short_name(self):
        if self.user_type == 'USER' and hasattr(self, 'user_profile'):
            return self.user_profile.first_name
        elif self.user_type == 'COURIER' and hasattr(self, 'courier_profile'):
            return self.courier_profile.first_name
        return self.email


class UserProfile(AbstractBaseModel):
    """
    Profile for regular customers.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # Add more customer-specific fields as needed

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"


class CourierProfile(AbstractBaseModel):
    """
    Profile for couriers/drivers.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='courier_profile'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    vehicle_registration = models.CharField(max_length=50, blank=True, null=True)
    is_available = models.BooleanField(default=False)
    current_location = models.JSONField(null=True, blank=True)
    # Add more courier-specific fields as needed

    class Meta:
        db_table = 'courier_profiles'
        verbose_name = 'Courier Profile'
        verbose_name_plural = 'Courier Profiles'

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.user.email}"

