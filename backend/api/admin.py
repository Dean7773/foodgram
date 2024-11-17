from django.contrib import admin

from foodgram.models import Tag, Ingredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Раздел тегов в админке."""
    list_display = ('name', 'slug')
    empty_value_display = 'значение отсутствует'
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Раздел ингредиентов в админке."""
    list_display = ('name',)
    empty_value_display = 'значение отсутствует'
    list_filter = ('name',)
    search_fields = ('name',)
