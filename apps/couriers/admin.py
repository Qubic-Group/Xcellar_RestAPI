from django.contrib import admin
from .models import Vehicle, DriverLicense


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'license_plate_number',
        'manufacturer',
        'model',
        'vehicle_type',
        'ownership_condition',
        'courier',
        'has_documents',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'vehicle_type',
        'ownership_condition',
        'is_active',
        'created_at',
    ]
    search_fields = [
        'license_plate_number',
        'manufacturer',
        'model',
        'courier__email',
        'courier__courier_profile__full_name',
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Courier Information', {
            'fields': ('courier',)
        }),
        ('Vehicle Information', {
            'fields': (
                'vehicle_type',
                'ownership_condition',
                'manufacturer',
                'model',
                'year_of_manufacturing',
                'license_plate_number',
            )
        }),
        ('Documents (Optional)', {
            'fields': (
                'registration_proof',
                'insurance_policy_proof',
                'road_worthiness_proof',
            ),
            'description': 'Upload vehicle documents. Allowed formats: PDF, DOC, DOCX, Images (JPG, PNG, etc.)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('courier')
    
    def has_documents(self, obj):
        """Check if vehicle has any documents uploaded"""
        docs = [
            bool(obj.registration_proof),
            bool(obj.insurance_policy_proof),
            bool(obj.road_worthiness_proof),
        ]
        return 'Yes' if any(docs) else 'No'
    has_documents.short_description = 'Has Documents'
    has_documents.boolean = False


@admin.register(DriverLicense)
class DriverLicenseAdmin(admin.ModelAdmin):
    list_display = [
        'courier_profile',
        'courier_email',
        'license_number',
        'issue_date',
        'expiry_date',
        'is_expired_status',
        'has_documents',
        'is_active',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'created_at',
    ]
    search_fields = [
        'license_number',
        'courier_profile__user__email',
        'courier_profile__full_name',
        'issuing_authority',
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Courier Information', {
            'fields': ('courier_profile',)
        }),
        ('License Information', {
            'fields': (
                'license_number',
                'issue_date',
                'expiry_date',
                'issuing_authority',
            )
        }),
        ('License Documents (Optional)', {
            'fields': (
                'front_page',
                'back_page',
            ),
            'description': 'Upload driver license documents. Allowed formats: PDF, DOC, DOCX, Images (JPG, PNG, etc.)'
        }),
        ('Vehicle Documents (Optional)', {
            'fields': (
                'vehicle_insurance',
                'vehicle_registration',
            ),
            'description': 'Upload vehicle insurance and registration documents. Allowed formats: PDF, DOC, DOCX, Images (JPG, PNG, etc.)'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('courier_profile', 'courier_profile__user')
    
    def courier_email(self, obj):
        """Get courier email"""
        return obj.courier_profile.user.email
    courier_email.short_description = 'Courier Email'
    
    def is_expired_status(self, obj):
        """Check if license is expired"""
        expired = obj.is_expired()
        if expired is None:
            return 'Unknown'
        return 'Yes' if expired else 'No'
    is_expired_status.boolean = True
    is_expired_status.short_description = 'Expired'
    
    def has_documents(self, obj):
        """Check if license has any documents uploaded"""
        docs = [
            bool(obj.front_page),
            bool(obj.back_page),
            bool(obj.vehicle_insurance),
            bool(obj.vehicle_registration),
        ]
        return 'Yes' if any(docs) else 'No'
    has_documents.short_description = 'Has Documents'
    has_documents.boolean = False

