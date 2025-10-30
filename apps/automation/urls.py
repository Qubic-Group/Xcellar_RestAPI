from django.urls import path
from .views import n8n_webhook, workflow_logs, automation_tasks

app_name = 'automation'

urlpatterns = [
    path('webhook/', n8n_webhook, name='n8n_webhook'),
    path('workflows/', workflow_logs, name='workflow_logs'),
    path('tasks/', automation_tasks, name='automation_tasks'),
]

