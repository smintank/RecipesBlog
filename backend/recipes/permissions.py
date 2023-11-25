from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class ReadOnlyOrNotMePath(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.path == '/api/users/me/':
            return request.user.is_authenticated
        return request.method in permissions.SAFE_METHODS
