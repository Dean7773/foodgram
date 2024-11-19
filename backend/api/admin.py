from django.contrib import admin

from foodgram.models import (Favorites, Ingredient, Recipe,
                             RecipeIngredient, Tag, ShoppingList)


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


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Раздел рецептов в админке."""
    list_display = ('name', 'author', 'text',
                    'cooking_time', 'pub_date', 'uniq_code')
    empty_value_display = 'значение отсутствует'
    list_filter = ('author', 'tags')
    search_fields = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Раздел ингредиентов рецепта в админке."""
    list_display = ('recipe', 'ingredient', 'amount')
    empty_value_display = 'значение отсутствует'
    list_filter = ('recipe', 'ingredient')
    search_fields = ('ingredient__name',)


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    """Раздел избранных рецептов в админке."""
    list_display = ('user', 'favorites')
    list_filter = ('user', 'favorites')
    search_fields = ('user__username', 'favorites__name')
    ordering = ('user', 'favorites')



@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """Раздел списка покупок в админке."""
    list_display = ('user', 'recipe')
    empty_value_display = 'значение отсутствует'
    list_filter = ('user',)
    search_fields = ('recipe__name',)
