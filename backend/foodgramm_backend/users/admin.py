from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email',
                    'first_name', 'last_name',
                    'recipes', 'follower')
    list_display_links = ('username',)
    list_editable = ('email',)
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')

    @admin.display(description='Подписчики')
    def follower(self, obj):
        return obj.follower.count()

    @admin.display(description='Рецепты')
    def recipes(self, obj):
        return obj.recipes.count()


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
