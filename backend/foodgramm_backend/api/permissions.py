
from rest_framework import permissions


class NotMeOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.get_full_path() == '/api/users/me/' and not request.user.is_authenticated:
            return False
        return (
                request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated
            )
