from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_password_reset_email(user, token):
    """
    Send password reset email to user.
    
    Args:
        user: User instance
        token: UUID token for password reset
    
    Returns:
        bool: True if email sent successfully
    
    Raises:
        Exception: If email sending fails
    """
    # Construct reset URL - handle both cases where PASSWORD_RESET_URL includes/excludes path
    base_url = getattr(settings, 'PASSWORD_RESET_URL', 'http://localhost:8000/reset-password')
    # Remove trailing slash and ensure proper format
    base_url = base_url.rstrip('/')
    if '/reset-password' not in base_url:
        reset_url = f"{base_url}/reset-password?token={token}"
    else:
        reset_url = f"{base_url}?token={token}"
    
    # Context for email template
    context = {
        'user': user,
        'reset_url': reset_url,
        'token': str(token),
        'expiry_minutes': getattr(settings, 'PASSWORD_RESET_TOKEN_EXPIRY', 15),
        'app_name': getattr(settings, 'APP_NAME', 'Xcellar'),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@xcellar.com'),
    }
    
    # Render HTML email
    try:
        html_message = render_to_string('accounts/password_reset/password_reset.html', context)
    except Exception as e:
        logger.error(f"Failed to render HTML email template: {e}")
        raise Exception("Failed to render email template")
    
    # Render plain text email
    try:
        plain_message = render_to_string('accounts/password_reset/password_reset.txt', context)
    except Exception as e:
        logger.error(f"Failed to render plain text email template: {e}")
        raise Exception("Failed to render email template")
    
    # Send email
    try:
        send_mail(
            subject=f'Reset Your {context["app_name"]} Password',
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@xcellar.com'),
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        raise
