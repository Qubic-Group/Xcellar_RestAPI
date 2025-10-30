from django.db import models
from apps.core.models import AbstractBaseModel


class WorkflowLog(AbstractBaseModel):
    """
    Model to track n8n workflow executions.
    """
    WORKFLOW_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    workflow_id = models.CharField(max_length=255)
    workflow_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=WORKFLOW_STATUS_CHOICES, default='PENDING')
    trigger_data = models.JSONField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    executed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_logs'
        ordering = ['-executed_at']
        verbose_name = 'Workflow Log'
        verbose_name_plural = 'Workflow Logs'

    def __str__(self):
        return f"{self.workflow_name or self.workflow_id} - {self.status}"


class AutomationTask(AbstractBaseModel):
    """
    Model to track automation tasks triggered from Django.
    """
    TASK_TYPE_CHOICES = [
        ('ORDER_CREATED', 'Order Created'),
        ('COURIER_ASSIGNED', 'Courier Assigned'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('CUSTOM', 'Custom'),
    ]

    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    workflow_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=WorkflowLog.WORKFLOW_STATUS_CHOICES, default='PENDING')
    input_data = models.JSONField(null=True, blank=True)
    output_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'automation_tasks'
        ordering = ['-created_at']
        verbose_name = 'Automation Task'
        verbose_name_plural = 'Automation Tasks'

    def __str__(self):
        return f"{self.task_type} - {self.status}"

