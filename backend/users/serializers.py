from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from users.models import Subscriptions

from foodgram.models import Recipe
from foodgram.utils import Base64ImageField

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
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('avatar',)

    def validate(self, value):
        if 'avatar' not in value or value['avatar'] is None:
            raise ValidationError('Необходимо добавить аватар.')
        return value
