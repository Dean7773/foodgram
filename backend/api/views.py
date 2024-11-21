from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthenticatedOrAuthorOrReadOnly
from api.serializers import (FavoritesSerializer, IngredientSerializer,
                             RecipeGetSerializer, RecipeCreateSerializer,
                             ShoppingListtSerializer, ShortRecipeSerializer,
                             TagSerializer, UserAvatarSerializer,
                             UserSubscribeSerializer,
                             UserSubscriptionsSerializer)
from foodgram.models import (Favorites, Ingredient, Recipe,
                             RecipeIngredient, ShoppingList, Tag)
from users.models import Subscriptions, User


class UserSubscriptionsViewSet(viewsets.ModelViewSet):
    """Обрабатывает подписки пользователей и возвращает информацию"""
    """о пользователях, на которых подписан текущий пользователь."""
    serializer_class = UserSubscriptionsSerializer
    http_method_names = ('get', )

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserViewSet(DjoserUserViewSet):
    """Управляет действиями над пользователями,"""
    """такими как создание подписок,"""
    """а также обновление и удаление аватаров."""
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        return (IsAuthenticated(),)

    @action(
        detail=False,
        methods=('GET', ),
        permission_classes=(IsAuthenticated, )
    )
    def me(self, request, *args, **kwargs):
        """Получить информацию о текущем пользователе."""
        return super().me(request, *args, **kwargs)

    @action(
        detail=False,
        methods=('POST', ),
        permission_classes=(IsAuthenticated, )
    )
    def subscribe(self, request, **kwargs):
        """Подписаться на пользователя."""
        following = get_object_or_404(User, id=kwargs['user_id'])
        serializer = UserSubscribeSerializer(
            data={'user': request.user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        """Отписаться от пользователя."""
        following = get_object_or_404(User, id=kwargs['user_id'])
        subscription_deleted, _ = Subscriptions.objects.filter(
            user=request.user,
            following=following
        ).delete()

        if not subscription_deleted:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('PUT', ),
        permission_classes=(IsAuthenticated, )
    )
    def upload_avatar(self, request):
        """Загрузить новый аватар пользователя."""
        serializer = UserAvatarSerializer(request.user, data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @upload_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удалить аватар пользователя."""
        if request.user.avatar:
            request.user.avatar.delete()
            return Response({'detail': 'Аватар успешно удален'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Аватар не найден'},
                        status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Позволяет управлять тегами, доступными в системе."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AllowAny, )
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Обрабатывает действия над ингредиентами и позволяет фильтровать их. """
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AllowAny, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами, позволяет получить"""
    """список рецептов, добавить, обновить или удалить рецепт,"""
    """а также для добавить в избранное и в список покупок."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrAuthorOrReadOnly, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от типа действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeCreateSerializer

    def create_method(self, request, recipe, data, item_serializer):
        serializer = item_serializer(data=data,
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ShortRecipeSerializer(recipe).data,
                        status=status.HTTP_201_CREATED)

    def delete_method(self, obj_model):
        deleted, _ = obj_model.delete()
        if not deleted:
            return Response(
                {'errors': 'Ошибка при удалении из списка покупок!'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated, )
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'favorites': recipe.id}

        if request.method == 'POST':
            return self.create_method(request, recipe,
                                      data, FavoritesSerializer)

        if request.method == 'DELETE':
            obj_model = Favorites.objects.filter(user=request.user,
                                                 favorites=recipe.id)
            return self.delete_method(obj_model)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated, )
    )
    def shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}

        if request.method == 'POST':
            return self.create_method(request, recipe,
                                      data, ShoppingListtSerializer)

        if request.method == 'DELETE':
            obj_model = ShoppingList.objects.filter(user=request.user,
                                                    recipe=recipe)
            return self.delete_method(obj_model)

    @action(
        detail=False,
        methods=('GET', ),
        permission_classes=(IsAuthenticated, )
    )
    def download_shopping_cart(self, request):
        """Генерация файла с закупочным списком."""
        ingredients_data = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')
        return self.create_shopping_list(ingredients_data)

    def create_shopping_list(self, ingredients_data):
        shopping_list_text = ['Закупочный список:\n']
        for item in ingredients_data:
            name = item['ingredient__name']
            unit = item['ingredient__measurement_unit']
            total_amount = item['total_amount']
            shopping_list_text.append(f'\n{name} - {total_amount}, {unit}')
        file_response = HttpResponse('\n'.join(shopping_list_text),
                                     content_type='text/plain')
        file_response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return file_response

    @action(
        detail=True,
        methods=('GET', ),
        url_path='get-link'
    )
    def retrieve_short_link(self, request, pk=None):
        """Создание короткой ссылки."""
        selected_recipe = get_object_or_404(Recipe, pk=pk)
        generated_link = request.build_absolute_uri(
            f'/s/{selected_recipe.uniq_code}/'
        )
        return Response({'short-link': generated_link},
                        status=status.HTTP_200_OK)
