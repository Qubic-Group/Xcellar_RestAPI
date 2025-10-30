from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, CourierProfile


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
    list_display = ['user', 'first_name', 'last_name', 'is_active']
    search_fields = ['first_name', 'last_name', 'user__email']


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'is_available', 'is_active']
    search_fields = ['first_name', 'last_name', 'user__email']
    list_filter = ['is_available', 'is_active']

