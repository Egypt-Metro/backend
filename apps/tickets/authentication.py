# apps/tickets/authentication.py
from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings


class ScannerAPIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication for scanner devices
    """
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_SCANNER_API_KEY')

        if not api_key:
            return None  # Let other authentication methods handle it

        # Simple API key validation - all scanners use the same key
        valid_api_key = getattr(settings, 'SCANNER_API_KEY', None)

        if api_key != valid_api_key:
            raise exceptions.AuthenticationFailed('Invalid scanner API key')

        # Return a scanner context without a user
        return (None, {'is_scanner': True})
