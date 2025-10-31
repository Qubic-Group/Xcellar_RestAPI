from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.conf import settings
import requests
import json
import uuid
import logging

from .models import PasswordResetToken

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def reset_password_page(request):
    """
    Password reset web page with deep linking support.
    GET /reset-password/?token=xxx
    """
    token = request.GET.get('token', '').strip()
    
    # Validate token exists and is valid UUID
    token_valid = False
    if token:
        try:
            # Validate UUID format
            uuid.UUID(token)
            reset_token = PasswordResetToken.objects.get(token=token)
            token_valid = reset_token.is_valid()
        except (ValueError, TypeError):
            # Invalid UUID format
            token_valid = False
        except PasswordResetToken.DoesNotExist:
            token_valid = False
        except Exception as e:
            logger.error(f"Error validating reset token: {e}")
            token_valid = False
    
    context = {
        'token': token,
        'token_valid': token_valid,
        'app_name': getattr(settings, 'APP_NAME', 'Xcellar'),
        'api_url': getattr(settings, 'API_BASE_URL', 'http://localhost:8000/api/v1'),
        'deep_link_scheme': getattr(settings, 'DEEP_LINK_SCHEME', 'xcellar'),
    }
    
    return render(request, 'accounts/password_reset/reset_password_page.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def reset_password_submit(request):
    """
    Handle password reset form submission from web page.
    POST /reset-password/submit/
    """
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        password = data.get('password', '').strip()
        password_confirm = data.get('password_confirm', '').strip()
        
        # Validate inputs
        if not token or not password or not password_confirm:
            return JsonResponse({'error': 'All fields are required'}, status=400)
        
        # Validate UUID format
        try:
            uuid.UUID(token)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid token format'}, status=400)
        
        if password != password_confirm:
            return JsonResponse({'error': 'Passwords do not match'}, status=400)
        
        if len(password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)
        
        # Call API endpoint
        api_url = f"{getattr(settings, 'API_BASE_URL', 'http://localhost:8000/api/v1')}/auth/password/reset/confirm/"
        
        try:
            response = requests.post(
                api_url,
                json={
                    'token': token,
                    'password': password,
                    'password_confirm': password_confirm
                },
                headers={'Content-Type': 'application/json'},
                timeout=10  # 10 second timeout
            )
        except requests.exceptions.Timeout:
            return JsonResponse({
                'success': False,
                'error': 'Request timeout. Please try again.'
            }, status=504)
        except requests.exceptions.ConnectionError:
            return JsonResponse({
                'success': False,
                'error': 'Unable to connect to server. Please try again later.'
            }, status=503)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error in password reset: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Network error. Please try again.'
            }, status=500)
        
        if response.status_code == 200:
            return JsonResponse({
                'success': True,
                'message': 'Password reset successfully!'
            })
        else:
            try:
                error_data = response.json()
                error_message = error_data.get('error', 'Failed to reset password')
            except (ValueError, KeyError):
                error_message = 'Failed to reset password'
            
            return JsonResponse({
                'success': False,
                'error': error_message
            }, status=response.status_code)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in password reset submit: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred. Please try again.'
        }, status=500)


