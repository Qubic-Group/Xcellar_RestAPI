from django.contrib import admin
from .models import Vehicle


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

