from django.contrib import admin

from foodgram.models import Ingredient, Tag


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
    list_display = ('name', 'measurement_unit')
    empty_value_display = 'значение отсутствует'
    list_filter = ('name', )
    search_fields = ('name', )
