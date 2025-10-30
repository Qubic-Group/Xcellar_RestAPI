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
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            user_type='USER',
            password=password,
            **validated_data
        )
        UserProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name
        )
        return user


class CourierRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for courier registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            user_type='COURIER',
            password=password,
            **validated_data
        )
        CourierProfile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details"""
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'user_type', 'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined']

    def get_profile(self, obj):
        if obj.user_type == 'USER' and hasattr(obj, 'user_profile'):
            return {
                'first_name': obj.user_profile.first_name,
                'last_name': obj.user_profile.last_name,
            }
        elif obj.user_type == 'COURIER' and hasattr(obj, 'courier_profile'):
            return {
                'first_name': obj.courier_profile.first_name,
                'last_name': obj.courier_profile.last_name,
                'is_available': obj.courier_profile.is_available,
            }
        return None

