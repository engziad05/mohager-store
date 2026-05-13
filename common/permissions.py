from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only access to everyone, write access only to staff."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsOwnerOrAdmin(permissions.BasePermission):
    """Allow object access only to the owner or an admin."""

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return getattr(obj, 'user', None) == request.user
