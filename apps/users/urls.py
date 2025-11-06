from django.urls import path

from .views import user_dashboard

app_name = 'users'

urlpatterns = [
    path('dashboard/', user_dashboard, name='user_dashboard'),
]

