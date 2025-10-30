from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import csrf_exempt
import logging

from .models import WorkflowLog, AutomationTask

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='100/h', method='POST')
def n8n_webhook(request):
    """
    Webhook endpoint for n8n to call Django APIs.
    This endpoint receives requests from n8n workflows.
    
    POST /api/v1/automation/webhook/
    
    Expected payload:
    {
        "action": "create_order",
        "data": {...}
    }
    """
    try:
        action = request.data.get('action')
        data = request.data.get('data', {})
        
        # Log the webhook call
        logger.info(f"Received n8n webhook: {action}")
        
        # Handle different actions from n8n
        if action == 'test':
            return Response({
                'status': 'success',
                'message': 'Webhook received successfully',
                'data': data
            }, status=status.HTTP_200_OK)
        
        # Add more action handlers here as needed
        # Example:
        # elif action == 'create_order':
        #     # Process order creation from n8n
        #     pass
        
        return Response({
            'status': 'success',
            'message': f'Action {action} received',
            'data': data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing n8n webhook: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='100/h', method='GET')
def workflow_logs(request):
    """
    Get workflow execution logs.
    GET /api/v1/automation/workflows/
    """
    logs = WorkflowLog.objects.all()[:50]  # Limit to last 50 logs
    return Response({
        'logs': [
            {
                'id': log.id,
                'workflow_id': log.workflow_id,
                'workflow_name': log.workflow_name,
                'status': log.status,
                'executed_at': log.executed_at
            }
            for log in logs
        ]
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='100/h', method='GET')
def automation_tasks(request):
    """
    Get automation tasks.
    GET /api/v1/automation/tasks/
    """
    tasks = AutomationTask.objects.all()[:50]  # Limit to last 50 tasks
    return Response({
        'tasks': [
            {
                'id': task.id,
                'task_type': task.task_type,
                'workflow_id': task.workflow_id,
                'status': task.status,
                'created_at': task.created_at
            }
            for task in tasks
        ]
    }, status=status.HTTP_200_OK)

