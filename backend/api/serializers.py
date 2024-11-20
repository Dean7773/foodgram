from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from foodgram.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                             ShoppingList, Tag)
from foodgram.utils import Base64ImageField
from users.models import Subscriptions

User = get_user_model()


class UserSignUpSerializer(UserCreateSerializer):
    """Сериализатор для регистрации пользователей."""
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password', 'role')


class UserInfoSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователе."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        return (user.is_authenticated
                and Subscriptions.objects.filter(
                    user=user, following=obj
                ).exists())


class UserSubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки или отписки от пользователей."""
    class Meta:
        model = Subscriptions
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=('user', 'following'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def to_representation(self, instance):
        request = self.context.get('request')
        return UserSubscriptionsSerializer(
            instance.following, context={'request': request}
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для получения краткой информации о рецепте."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSubscriptionsSerializer(UserSerializer):
    """Сериализатор для получения информации о подписках."""
    is_subscribed = serializers.SerializerMethodField()
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    avatar = Base64ImageField(required=False, allow_null=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')
        read_only_fields = ('email', 'username', 'first_name',
                            'last_name', 'is_subscribed', 'recipes',
                            'recipes_count', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        user = request.user
        return (user.is_authenticated
                and Subscriptions.objects.filter(
                    user=user, following=obj
                ).exists())

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для загрузки аватара."""
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, value):
        if 'avatar' not in value or value['avatar'] is None:
            raise ValidationError('Необходимо добавить аватар.')
        return value


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
    """Сериализатор для работы с ингредиентами в рецепте."""
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
    """Сериализатор для работы с избранным."""
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
    """Сериализатор для работы со списком покупок."""
    class Meta:
        model = ShoppingList
        fields = '__all__'
