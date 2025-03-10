# apps/trains/api/permissions.py

from rest_framework import permissions


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class CanUpdateCrowdLevel(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'update_crowd_level':
            return request.user and request.user.has_perm('trains.can_update_crowd_level')
        return True
