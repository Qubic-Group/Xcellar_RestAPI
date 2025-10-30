from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import UserProfile, CourierProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer to include user_type in token payload.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type
        token['email'] = user.email
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Confirm password - must match password'
    )
    full_name = serializers.CharField(
        write_only=True,
        help_text='User full name'
    )
    email = serializers.EmailField(
        help_text='User email address (must be unique)'
    )
    phone_number = serializers.CharField(
        help_text='Phone number in international format (e.g., +1234567890)'
    )

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password', 'password_confirm', 'full_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        full_name = validated_data.pop('full_name')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            user_type='USER',
            password=password,
            **validated_data
        )
        UserProfile.objects.create(
            user=user,
            full_name=full_name
        )
        return user


class CourierRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for courier registration"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Confirm password - must match password'
    )
    full_name = serializers.CharField(
        write_only=True,
        help_text='Courier full name'
    )
    email = serializers.EmailField(
        help_text='Courier email address (must be unique)'
    )
    phone_number = serializers.CharField(
        help_text='Phone number in international format (e.g., +1234567890)'
    )

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password', 'password_confirm', 'full_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        full_name = validated_data.pop('full_name')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            user_type='COURIER',
            password=password,
            **validated_data
        )
        CourierProfile.objects.create(
            user=user,
            full_name=full_name
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'user_type', 'date_joined', 'full_name']
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        if obj.user_type == 'USER' and hasattr(obj, 'user_profile'):
            return obj.user_profile.full_name
        elif obj.user_type == 'COURIER' and hasattr(obj, 'courier_profile'):
            return obj.courier_profile.full_name
        return None

