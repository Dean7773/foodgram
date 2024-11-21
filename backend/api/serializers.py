from django.contrib.auth import get_user_model
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from foodgram.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                             ShoppingList, Tag)
from api.fields import Base64ImageField
from users.models import Subscriptions

User = get_user_model()


class UserInfoSerializer(UserSerializer):
    """Сериализатор для получения информации о пользователе."""
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return (request and obj.is_authenticated
                and Subscriptions.objects.filter(
                    user=request.user, following=obj
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

    def validate(self, attrs):
        request = self.context.get('request')
        following = attrs.get('following')

        if request.user == following:
            raise serializers.ValidationError(
                'Подписка на себя недопустима!'
            )
        return attrs

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


class UserSubscriptionsSerializer(UserInfoSerializer):
    """Сериализатор для получения информации о подписках."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count', 'avatar')
        read_only_fields = ('email', 'username', 'first_name',
                            'last_name', 'is_subscribed', 'recipes',
                            'recipes_count', 'avatar')

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, instance):
        request = self.context.get('request')
        recipe_limit = request.GET.get('recipes_limit')
        all_recipes = instance.recipes.all()
        if recipe_limit:
            try:
                recipe_limit = int(recipe_limit)
                all_recipes = all_recipes[:recipe_limit]
            except ValueError:
                pass
        recipe_data = ShortRecipeSerializer(all_recipes, many=True).data
        return recipe_data


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
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='recipeingredient')
    image = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'ingredients', 'name',
                  'image', 'text', 'cooking_time')

    def check_duplicates(self, item_list, item_type):
        """Проверка на дублирование элементов по заданному ключу."""
        if len(set(item_list)) != len(item_list):
            raise serializers.ValidationError(
                f'Вы пытаетесь добавить в рецепт два одинаковых {item_type}.'
            )

    def validate(self, data):
        """Проверка входных данных на корректность."""

        # Проверка ингредиентов
        ingredients_data = data.get('recipeingredient')
        if not ingredients_data:
            raise serializers.ValidationError('Не указаны ингредиенты.')
        item_list = []
        for item in ingredients_data:
            item_list.append(item.get('ingredient')['id'])
        self.check_duplicates(item_list, 'ингредиенты')

        # Проверка тегов
        tags_data = data.get('tags')
        if not tags_data:
            raise serializers.ValidationError('Не указаны теги.')
        item_list = []
        for item in tags_data:
            item_list.append(item.id)
        self.check_duplicates(item_list, 'теги')

        return data

    def validate_image(self, value):
        # Проверка наличия поля image.
        if value is None or value == '':
            raise serializers.ValidationError('Отсутствует картинка.')
        return value

    def ingredient_tag_instance(self, recipe, data):
        ingredient_instances = []
        for ingredient in data:
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

    @transaction.atomic
    def create(self, validated_data):
        """Создание нового рецепта."""
        user = self.context['request'].user
        ingredients_data = validated_data.pop('recipeingredient')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        self.ingredient_tag_instance(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients_data = validated_data.pop('recipeingredient', None)
        tags = validated_data.get('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.ingredient_tag_instance(instance, ingredients_data)
        return super().update(instance, validated_data)

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
        return (request and request.user.is_authenticated
                and Favorites.objects.filter(user=request.user,
                                             favorites=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and ShoppingList.objects.filter(user=request.user,
                                                recipe=obj).exists())


class FavoritesSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с избранным."""
    class Meta:
        model = Favorites
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Favorites.objects.all(),
                fields=['user', 'favorites'],
                message='Рецепт уже добавлен в избранное.'
            )
        ]


class ShoppingListtSerializer(serializers.ModelSerializer):
    """Сериализатор для работы со списком покупок."""
    class Meta:
        model = ShoppingList
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=['user', 'recipe'],
                message='Рецепт уже добавлен в корзину!'
            )
        ]
