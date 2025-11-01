from django.contrib import admin
from .models import WorkflowLog, AutomationTask


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ['workflow_name', 'workflow_id', 'status', 'executed_at', 'created_at']
    list_filter = ['status', 'executed_at', 'created_at']
    search_fields = ['workflow_id', 'workflow_name']
    readonly_fields = ['executed_at', 'created_at', 'updated_at']
    ordering = ['-executed_at']
    
    fieldsets = (
        ('Workflow Information', {
            'fields': (
                'workflow_id',
                'workflow_name',
                'status',
            )
        }),
        ('Data', {
            'fields': (
                'trigger_data',
                'response_data',
                'error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('executed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    list_display = ['task_type', 'workflow_id', 'status', 'created_at', 'updated_at']
    list_filter = ['task_type', 'status', 'created_at']
    search_fields = ['workflow_id', 'task_type', 'error_message']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Task Information', {
            'fields': (
                'task_type',
                'workflow_id',
                'status',
            )
        }),
        ('Data', {
            'fields': (
                'input_data',
                'output_data',
                'error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

