"""
API response utilities for BancaFiel backend
Standardized response formatting for API Gateway
"""
import json


def success_response(data, status_code=200):
    """
    Standard success response for API Gateway.

    Args:
        data: Response data (will be JSON serialized)
        status_code (int): HTTP status code

    Returns:
        dict: API Gateway response object
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(data, default=str)  # default=str handles datetime
    }


def error_response(message, status_code=400, error_code=None):
    """
    Standard error response for API Gateway.

    Args:
        message (str): Error message
        status_code (int): HTTP status code
        error_code (str): Optional error code

    Returns:
        dict: API Gateway response object
    """
    error_body = {
        'error': True,
        'message': message
    }

    if error_code:
        error_body['error_code'] = error_code

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(error_body)
    }


def created_response(data, location=None):
    """Response for created resources (201)"""
    response = success_response(data, 201)
    if location:
        response['headers']['Location'] = location
    return response


def not_found_response(message="Resource not found"):
    """404 Not Found response"""
    return error_response(message, 404, 'NOT_FOUND')


def unauthorized_response(message="Unauthorized"):
    """401 Unauthorized response"""
    return error_response(message, 401, 'UNAUTHORIZED')


def forbidden_response(message="Forbidden"):
    """403 Forbidden response"""
    return error_response(message, 403, 'FORBIDDEN')


def validation_error_response(errors):
    """
    400 Bad Request with validation errors.

    Args:
        errors (list or dict): Validation error details
    """
    return {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': True,
            'message': 'Validation failed',
            'validation_errors': errors
        })
    }
