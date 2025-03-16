# apps/dashboard/api/permissions.py

from rest_framework import permissions


class IsSuperUserOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow superusers or staff
    """
    def has_permission(self, request, view):
        # Allow read-only access to staff
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_staff

        # Full access only to superusers
        return request.user.is_superuser


class IsAdminWithSpecificPermissions(permissions.BasePermission):
    """
    Granular permission control for different actions
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Different permission levels for different actions
        if view.action in ['list', 'retrieve']:
            return request.user.is_staff
        elif view.action in ['create', 'update', 'partial_update', 'destroy']:
            return request.user.is_superuser

        return False
