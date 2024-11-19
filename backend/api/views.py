from api.filters import IngredientFilter, RecipeFilter
from api.serializers import (IngredientSerializer, RecipeGetSerializer,
                             RecipeSerializer, ShoppingListtSerializer,
                             TagSerializer)
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from users.models import Subscriptions, User
from users.serializers import (ShortRecipeSerializer, UserAvatarSerializer,
                               UserSubscribeSerializer,
                               UserSubscriptionsSerializer)

from foodgram.models import (Favorites, Ingredient, Recipe,
                             RecipeIngredient, ShoppingList, Tag)


class UserSubscriptionsViewSet(viewsets.ModelViewSet):
    """Обрабатывает подписки пользователей и возвращает информацию"""
    """о пользователях, на которых подписан текущий пользователь."""
    serializer_class = UserSubscriptionsSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    """Управляет действиями над пользователями,"""
    """такими как создание подписок,"""
    """а также обновление и удаление аватаров."""
    queryset = User.objects.all()

    def create(self, request, **kwargs):
        """Подписаться на пользователя."""
        following = get_object_or_404(User, id=kwargs['user_id'])
        serializer = UserSubscribeSerializer(
            data={'user': request.user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, **kwargs):
        """Отписаться от пользователя."""
        following = get_object_or_404(User, id=kwargs['user_id'])
        subscription = Subscriptions.objects.filter(
            user=request.user,
            following=following
        ).first()

        if not subscription:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put'],
        permission_classes=[IsAuthenticated,]
    )
    def upload_avatar(self, request):
        """Загрузить новый аватар пользователя."""
        serializer = UserAvatarSerializer(request.user, data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['delete'],
        permission_classes=[IsAuthenticated,]
    )
    def delete_avatar(self, request):
        """Удалить аватар пользователя."""
        if request.user.avatar:
            request.user.avatar.delete()
            return Response({'detail': 'Аватар успешно удален'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Аватар не найден'},
                        status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ModelViewSet):
    """Позволяет управлять тегами, доступными в системе."""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny,]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Обрабатывает действия над ингредиентами и позволяет фильтровать их. """
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny,]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для управления рецептами, позволяет получить"""
    """список рецептов, добавить, обновить или удалить рецепт,"""
    """а также для добавить в избранное и в список покупок."""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от типа действия."""
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated,]
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта из избранного."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorites.objects.filter(user=request.user,
                                        favorites=recipe).exists():
                return Response({'статус': 'Рецепт уже добавлен в избранное.'},
                                status=status.HTTP_400_BAD_REQUEST)
            Favorites.objects.create(user=request.user, favorites=recipe)
            return Response({'статус': 'Рецепт добавлен в избранное.'})

        if request.method == 'DELETE':
            Favorites.objects.filter(user=request.user,
                                     favorites=recipe).delete()
            return Response({'статус': 'Рецепт удален из избранных.'})

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated,]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление или удаление рецепта из списка покупок."""
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'recipe': recipe.id, 'user': request.user.id}
        if request.method == 'POST':
            serializer = ShoppingListtSerializer(data=data,
                                                 context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(ShortRecipeSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            deleted, _ = ShoppingList.objects.filter(user=request.user,
                                                     recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': 'Ошибка при удалении из списка покупок!'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, ]
    )
    def download_shopping_cart(self, request):
        """Генерация файла с закупочным списком."""
        ingredients_data = RecipeIngredient.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))

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
        methods=['get'],
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


class ShortLinkViewSet(viewsets.ViewSet):
    """Обработка коротких ссылок для рецептов."""
    def short_link_redirect(self, request, short_link=None):
        recipe = get_object_or_404(Recipe, uniq_code=short_link)
        full_url = request.build_absolute_uri(f'/recipes/{recipe.id}')
        return redirect(full_url)
