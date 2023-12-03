from rest_framework import permissions


class ReadOnlyOrNotMePath(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.path == '/api/users/me/':
            return request.user.is_authenticated
        return request.method in permissions.SAFE_METHODS
