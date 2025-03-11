# apps/trains/api/permissions.py

from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsStaffOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class CanUpdateCrowdLevel(permissions.BasePermission):
    """
    Custom permission to allow only authenticated users
    or staff members to update crowd levels.
    """
    def has_permission(self, request, view):
        # Log detailed permission check
        logger.info(f"Permission check for user: {request.user}")
        logger.info(f"Is Authenticated: {request.user.is_authenticated}")
        logger.info(f"Is Staff: {request.user.is_staff}")

        # Allow authenticated users with staff or superuser status
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )

    def has_object_permission(self, request, view, obj):
        # Additional object-level permissions
        logger.info(f"Object-level permission check for {obj}")
        return (
            request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )
