from typing import Dict, Any, Optional
from django.conf import settings
import logging

from .n8n_client import N8nClient
from ..models import WorkflowLog, AutomationTask

logger = logging.getLogger(__name__)


class WorkflowTrigger:
    """
    Service to trigger n8n workflows from Django events.
    Handles Django -> n8n communication.
    """
    
    def __init__(self):
        self.n8n_client = N8nClient()
    
    def trigger_workflow(self, workflow_id: str, data: Dict[str, Any], 
                        workflow_name: Optional[str] = None) -> WorkflowLog:
        """
        Trigger a n8n workflow and log the execution.
        
        Args:
            workflow_id: n8n workflow ID or webhook URL
            data: Data to send to the workflow
            workflow_name: Optional workflow name for logging
            
        Returns:
            WorkflowLog instance
        """
        workflow_log = WorkflowLog.objects.create(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status='PENDING',
            trigger_data=data
        )
        
        try:
            # Check if it's a webhook URL or workflow ID
            if workflow_id.startswith('http'):
                response = self.n8n_client.trigger_workflow_webhook(workflow_id, data)
            else:
                response = self.n8n_client.trigger_workflow_by_id(workflow_id, data)
            
            if response is not None:
                workflow_log.status = 'SUCCESS'
                workflow_log.response_data = response
            else:
                workflow_log.status = 'FAILED'
                workflow_log.error_message = 'Failed to get response from n8n'
        except Exception as e:
            workflow_log.status = 'FAILED'
            workflow_log.error_message = str(e)
            logger.error(f"Error triggering workflow {workflow_id}: {e}")
        
        workflow_log.save()
        return workflow_log
    
    def create_automation_task(self, task_type: str, workflow_id: str, 
                              input_data: Dict[str, Any]) -> AutomationTask:
        """
        Create an automation task and trigger workflow.
        
        Args:
            task_type: Type of task (from AutomationTask.TASK_TYPE_CHOICES)
            workflow_id: n8n workflow ID or webhook URL
            input_data: Input data for the workflow
            
        Returns:
            AutomationTask instance
        """
        task = AutomationTask.objects.create(
            task_type=task_type,
            workflow_id=workflow_id,
            status='PENDING',
            input_data=input_data
        )
        
        try:
            workflow_log = self.trigger_workflow(workflow_id, input_data)
            task.status = workflow_log.status
            task.output_data = workflow_log.response_data
            if workflow_log.error_message:
                task.error_message = workflow_log.error_message
        except Exception as e:
            task.status = 'FAILED'
            task.error_message = str(e)
            logger.error(f"Error creating automation task {task_type}: {e}")
        
        task.save()
        return task
    
    # Convenience methods for common events
    def on_order_created(self, order_data: Dict[str, Any], workflow_id: str):
        """Trigger workflow when order is created"""
        return self.create_automation_task(
            'ORDER_CREATED',
            workflow_id,
            {'event': 'order_created', 'order': order_data}
        )
    
    def on_courier_assigned(self, order_data: Dict[str, Any], 
                           courier_data: Dict[str, Any], workflow_id: str):
        """Trigger workflow when courier is assigned"""
        return self.create_automation_task(
            'COURIER_ASSIGNED',
            workflow_id,
            {
                'event': 'courier_assigned',
                'order': order_data,
                'courier': courier_data
            }
        )
    
    def on_status_changed(self, entity_type: str, entity_id: str, 
                         old_status: str, new_status: str, workflow_id: str):
        """Trigger workflow when status changes"""
        return self.create_automation_task(
            'STATUS_CHANGED',
            workflow_id,
            {
                'event': 'status_changed',
                'entity_type': entity_type,
                'entity_id': entity_id,
                'old_status': old_status,
                'new_status': new_status
            }
        )

