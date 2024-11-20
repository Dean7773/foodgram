from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from users.models import Subscriptions

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Раздел пользователей в админке."""
    list_display = ('pk', 'email', 'username', 'first_name',
                    'last_name', 'display_avatar')
    empty_value_display = 'значение отсутствует'
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {
            'fields': (
                'username', 'email', 'password',
                'first_name', 'last_name', 'avatar'
            )
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'avatar', 'is_active', 'is_staff'),
        }),
    )

    def display_avatar(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height: auto;" />',
                obj.avatar.url
            )
        return 'Нет аватара'


@admin.register(Subscriptions)
class SubscribeAdmin(admin.ModelAdmin):
    """Раздел подписок в админке."""
    list_display = ('pk', 'user', 'following',)
    empty_value_display = 'значение отсутствует'
    search_fields = ('user', 'following')
