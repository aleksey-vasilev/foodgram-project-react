
from rest_framework import permissions
from .constants import USERS_ME_PATH


class NotMeOrReadOnly(permissions.BasePermission):
    """ Запрет обращение к USERS_ME_PATH для анонима """
    def has_permission(self, request, view):
        if (request.get_full_path() == USERS_ME_PATH
                and not request.user.is_authenticated):
            return False
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """ Разрешение для автора или только для чтения """
    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (obj.author == request.user
                or request.method in permissions.SAFE_METHODS)
