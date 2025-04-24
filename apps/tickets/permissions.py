# apps/tickets/permissions.py
from rest_framework import permissions


class IsAuthenticatedOrScanner(permissions.BasePermission):
    """
    Allow access to authenticated users or scanner devices
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        user_auth = bool(request.user and request.user.is_authenticated)

        # Check if scanner is authenticated
        scanner_auth = bool(
            hasattr(request, 'auth')
            and request.auth
            and isinstance(request.auth, dict)
            and request.auth.get('is_scanner')
        )

        return user_auth or scanner_auth
