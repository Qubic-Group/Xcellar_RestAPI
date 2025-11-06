from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
import logging

logger = logging.getLogger(__name__)


def get_user_friendly_error_message(exc):
    """
    Convert technical errors to user-friendly messages.
    """
    error_str = str(exc).lower()
    
    # Database integrity errors
    if isinstance(exc, IntegrityError):
        if 'duplicate key' in error_str or 'unique constraint' in error_str:
            if 'paystack_recipient_code' in error_str or 'recipient_code' in error_str:
                return 'Bank account details already exist. Please use a different account.'
            elif 'account_number' in error_str:
                return 'This bank account is already registered. Please use a different account.'
            elif 'email' in error_str:
                return 'This email address is already registered. Please use a different email.'
            elif 'phone_number' in error_str:
                return 'This phone number is already registered. Please use a different phone number.'
            elif 'license_plate' in error_str:
                return 'This vehicle license plate number is already registered.'
            elif 'username' in error_str:
                return 'This username is already taken. Please choose a different one.'
            else:
                return 'This information already exists. Please use different details.'
    
    # Validation errors
    if isinstance(exc, (DjangoValidationError, DRFValidationError)):
        # If it's already a dict/list, return as is (DRF will handle formatting)
        if isinstance(exc.detail, (dict, list)):
            return exc.detail
        return str(exc)
    
    # Permission errors
    if 'permission' in error_str or 'forbidden' in error_str:
        return 'You do not have permission to perform this action.'
    
    # Authentication errors
    if 'authentication' in error_str or 'unauthorized' in error_str or 'invalid token' in error_str:
        return 'Authentication required. Please log in and try again.'
    
    # Not found errors
    if 'not found' in error_str or 'does not exist' in error_str:
        return 'The requested resource was not found.'
    
    # Default: return original message
    return str(exc)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns user-friendly error responses.
    """
    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        logger.warning(f"IntegrityError in {context.get('view', {}).__class__.__name__}: {exc}")
        user_message = get_user_friendly_error_message(exc)
        return Response(
            {
                'error': user_message if isinstance(user_message, str) else user_message
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        user_message = get_user_friendly_error_message(exc)
        return Response(
            {
                'error': user_message if isinstance(user_message, str) else user_message
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Use DRF's default exception handler
    response = exception_handler(exc, context)

    if response is not None:
        # Get user-friendly message
        user_message = get_user_friendly_error_message(exc)
        
        # Format response consistently
        if isinstance(user_message, (dict, list)):
            # Already formatted by DRF
            custom_response_data = {
                'error': user_message
            }
        else:
            custom_response_data = {
                'error': user_message
            }
        
        response.data = custom_response_data

    return response

