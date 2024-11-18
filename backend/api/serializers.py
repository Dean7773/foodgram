from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from users.serializers import UserInfoSerializer

from foodgram.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                             ShoppingList, Tag)
from foodgram.utils import Base64ImageField

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='recipeingredient')
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')

    def validate_ingredients(self, value):
        """Проверка ингредиентов на корректность."""
        if not value:
            raise serializers.ValidationError('Не указаны ингредиенты.')
        for ingredient in value:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    'Количество должно быть больше 0.'
                )
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Создание нового рецепта."""
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipeingredient', None)
        if ingredients_data is None:
            raise serializers.ValidationError("Ингредиенты не указаны.")
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        ingredient_instances = []
        for ingredient in ingredients_data:
            ingredient_id = ingredient['ingredient']['id'].id
            amount = ingredient['amount']
            ingredient_instances.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_id,
                    amount=amount
                )
            )
        RecipeIngredient.objects.bulk_create(ingredient_instances)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients_data = validated_data.pop('recipeingredient', None)
        if ingredients_data is None:
            raise serializers.ValidationError("Ингредиенты не указаны.")
        tags = validated_data.get('tags')
        instance.tags.clear()
        if tags:
            instance.tags.set(tags)
        instance.ingredients.clear()
        ingredient_instances = [
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient['ingredient']['id'].id,
                amount=ingredient['amount']
            )
            for ingredient in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredient_instances)
        super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        """Пользовательское представление объекта."""
        return RecipeGetSerializer(instance, context=self.context).data


class RecipeGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения информации о рецептах."""
    tags = TagSerializer(many=True, read_only=True)
    author = UserInfoSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='recipeingredient')
    image = Base64ImageField(required=False, allow_null=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and Favorites.objects.filter(user=request.user,
                                             favorites=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request.user.is_authenticated
                and ShoppingList.objects.filter(user=request.user,
                                                recipe=obj).exists())


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с краткой информацией о рецепте."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorites
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=('user', 'favorites'),
                message='Рецепт уже в избранном.'
            )
        ]


class ShoppingListtSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingList
        fields = '__all__'
