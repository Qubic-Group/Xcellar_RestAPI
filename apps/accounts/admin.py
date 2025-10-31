from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, CourierProfile
from .password_reset.models import PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'phone_number', 'user_type', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff']
    search_fields = ['email', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number')}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'has_address', 'has_profile_image', 'is_active']
    search_fields = ['full_name', 'user__email', 'address']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name')
        }),
        ('Profile Details', {
            'fields': ('address', 'profile_image')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )
    
    def has_address(self, obj):
        """Check if profile has address"""
        return 'Yes' if obj.address else 'No'
    has_address.boolean = True
    has_address.short_description = 'Has Address'
    
    def has_profile_image(self, obj):
        """Check if profile has image"""
        return 'Yes' if obj.profile_image else 'No'
    has_profile_image.boolean = True
    has_profile_image.short_description = 'Has Image'


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'is_available', 'has_address', 'has_profile_image', 'is_active']
    search_fields = ['full_name', 'user__email', 'address', 'license_number']
    list_filter = ['is_available', 'is_active']
    
    fieldsets = (
        ('Courier Information', {
            'fields': ('user', 'full_name', 'license_number')
        }),
        ('Profile Details', {
            'fields': ('address', 'profile_image')
        }),
        ('Vehicle Information', {
            'fields': ('vehicle_type', 'vehicle_registration'),
            'classes': ('collapse',)
        }),
        ('Status & Location', {
            'fields': ('is_available', 'current_location')
        }),
        ('System', {
            'fields': ('is_active',)
        }),
    )
    
    def has_address(self, obj):
        """Check if profile has address"""
        return 'Yes' if obj.address else 'No'
    has_address.boolean = True
    has_address.short_description = 'Has Address'
    
    def has_profile_image(self, obj):
        """Check if profile has image"""
        return 'Yes' if obj.profile_image else 'No'
    has_profile_image.boolean = True
    has_profile_image.short_description = 'Has Image'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'email', 'is_used', 'is_expired', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email', 'user__email', 'token']
    readonly_fields = ['token', 'created_at', 'used_at']
    ordering = ['-created_at']
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

