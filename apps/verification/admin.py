from django.contrib import admin
from .models import PhoneVerification


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'verification_method', 'is_verified', 'attempts', 'created_at', 'expires_at']
    list_filter = ['is_verified', 'verification_method', 'created_at']
    search_fields = ['phone_number']
    readonly_fields = ['created_at', 'updated_at', 'verified_at', 'code_hash']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Verification Info', {
            'fields': ('phone_number', 'verification_method', 'code_hash')
        }),
        ('Status', {
            'fields': ('is_verified', 'verified_at', 'attempts', 'max_attempts')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at')
        }),
    )

