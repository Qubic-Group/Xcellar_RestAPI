import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class N8nClient:
    """
    Client to interact with n8n API/webhooks.
    Used for Django -> n8n communication.
    """
    
    def __init__(self):
        self.api_url = settings.N8N_API_URL
        self.api_key = settings.N8N_API_KEY
        self.webhook_secret = settings.N8N_WEBHOOK_SECRET
    
    def trigger_workflow_webhook(self, webhook_url: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Trigger a n8n workflow via webhook URL.
        
        Args:
            webhook_url: Full webhook URL from n8n
            data: Data to send to the workflow
            
        Returns:
            Response data or None if failed
        """
        try:
            headers = {}
            if self.webhook_secret:
                headers['X-n8n-webhook-secret'] = self.webhook_secret
            
            response = requests.post(
                webhook_url,
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger n8n webhook: {e}")
            return None
    
    def trigger_workflow_by_id(self, workflow_id: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Trigger a n8n workflow by ID using n8n API.
        
        Args:
            workflow_id: n8n workflow ID
            data: Data to send to the workflow
            
        Returns:
            Response data or None if failed
        """
        try:
            url = f"{self.api_url}/api/v1/workflows/{workflow_id}/execute"
            headers = {
                'Content-Type': 'application/json',
            }
            if self.api_key:
                headers['X-N8N-API-KEY'] = self.api_key
            
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to trigger n8n workflow {workflow_id}: {e}")
            return None

