# apps/trains/api/permissions.py

from rest_framework import permissions


class IsTrainOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("trains.can_operate_train")


class IsScheduleManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.has_perm("trains.can_manage_schedules")
