from django.contrib import admin

from users.models import User, Subscriptions


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Раздел пользователей в админке."""
    list_display = ('pk', 'email', 'username',
                    'first_name', 'last_name', 'role')
    empty_value_display = 'значение отсутствует'
    list_filter = ('username', 'email')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Subscriptions)
class CategoryAdmin(admin.ModelAdmin):
    """Раздел категорий в админке."""
    list_display = ('pk', 'user', 'following',)
    empty_value_display = 'значение отсутствует'
    list_filter = ('user', 'following')
    search_fields = ('user', 'following')
