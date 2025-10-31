from django.urls import path
from .web_views import reset_password_page, reset_password_submit

app_name = 'password_reset_web'

urlpatterns = [
    path('', reset_password_page, name='reset_password_page'),
    path('submit/', reset_password_submit, name='reset_password_submit'),
]

