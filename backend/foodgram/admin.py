from django.contrib import admin
from foodgram.models import Favorites


@admin.register(Favorites)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'favorites')
    list_filter = ('user', 'favorites')
    search_fields = ('user__username', 'favorites__name')
    ordering = ('user', 'favorites')
