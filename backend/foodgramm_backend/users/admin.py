from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import TokenProxy

admin.site.empty_value_display = 'Не задано'

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'password')
    list_editable = ('email',)
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')


admin.site.unregister(Group)
admin.site.unregister(TokenProxy)
