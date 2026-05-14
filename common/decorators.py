from django_ratelimit.decorators import ratelimit
from django.core.exceptions import PermissionDenied


def rate_limit_auth(func):
    """
    Rate limit decorator for authentication endpoints.
    Limits to 5 requests per minute per IP address.
    """
    return ratelimit(key='ip', rate='5/m', block=True)(func)


def rate_limit_email(func):
    """
    Rate limit decorator for email-related endpoints.
    Limits to 3 requests per hour per IP address.
    """
    return ratelimit(key='ip', rate='3/h', block=True)(func)
