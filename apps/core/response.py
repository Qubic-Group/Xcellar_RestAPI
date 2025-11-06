"""
Standardized response utilities for consistent API responses.
"""
from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Create a standardized success response.
    
    Args:
        data: Response data (dict, list, or None)
        message: Success message (string)
        status_code: HTTP status code (default: 200)
    
    Returns:
        Response object with standardized format
    """
    response_data = {
        'status': status_code,
    }
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        # If data is a dict, merge it into response
        if isinstance(data, dict):
            response_data.update(data)
        else:
            # Otherwise, add as 'data' key
            response_data['data'] = data
    
    return Response(response_data, status=status_code)


def error_response(error_message, status_code=status.HTTP_400_BAD_REQUEST, data=None):
    """
    Create a standardized error response.
    
    Args:
        error_message: Error message (string)
        status_code: HTTP status code (default: 400)
        data: Additional error data (dict, optional)
    
    Returns:
        Response object with standardized format
    """
    response_data = {
        'status': status_code,
        'error': error_message
    }
    
    if data:
        response_data.update(data)
    
    return Response(response_data, status=status_code)


def created_response(data=None, message=None):
    """Create a standardized 201 Created response."""
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def not_found_response(message='Resource not found'):
    """Create a standardized 404 Not Found response."""
    return error_response(message, status_code=status.HTTP_404_NOT_FOUND)


def unauthorized_response(message='Authentication required'):
    """Create a standardized 401 Unauthorized response."""
    return error_response(message, status_code=status.HTTP_401_UNAUTHORIZED)


def forbidden_response(message='You do not have permission to perform this action'):
    """Create a standardized 403 Forbidden response."""
    return error_response(message, status_code=status.HTTP_403_FORBIDDEN)


def validation_error_response(errors, message='Validation error'):
    """
    Create a standardized validation error response.
    
    Args:
        errors: Validation errors (dict or list from serializer.errors)
        message: Error message (string)
    
    Returns:
        Response object with standardized format
    """
    response_data = {
        'status': status.HTTP_400_BAD_REQUEST,
        'error': message,
        'errors': errors
    }
    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

