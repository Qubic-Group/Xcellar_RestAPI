from django.contrib import admin
from .models import WorkflowLog, AutomationTask


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ['workflow_name', 'workflow_id', 'status', 'executed_at']
    list_filter = ['status', 'executed_at']
    search_fields = ['workflow_id', 'workflow_name']
    readonly_fields = ['executed_at']
    ordering = ['-executed_at']


@admin.register(AutomationTask)
class AutomationTaskAdmin(admin.ModelAdmin):
    list_display = ['task_type', 'workflow_id', 'status', 'created_at']
    list_filter = ['task_type', 'status', 'created_at']
    search_fields = ['workflow_id', 'task_type']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

