from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (AllowAny, IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.serializers import (IngredientSerializer, RecipeGetSerializer,
                             RecipeSerializer, ShoppingListtSerializer,
                             TagSerializer)
from foodgram.models import Favorites, Ingredient, Recipe, ShoppingList, Tag
from users.models import Subscriptions
from users.serializers import (ShortRecipeSerializer, UserAvatarSerializer,
                               UserSubscribeSerializer,
                               UserSubscriptionsSerializer)

User = get_user_model()


class UserSubscriptionsViewSet(viewsets.ModelViewSet):
    serializer_class = UserSubscriptionsSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def create(self, request, **kwargs):
        following = get_object_or_404(User, id=kwargs['user_id'])
        serializer = UserSubscribeSerializer(
            data={'user': request.user.id, 'following': following.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, **kwargs):
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
        if request.user.avatar:
            request.user.avatar.delete()
            return Response({'detail': 'Аватар успешно удален'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'detail': 'Аватар не найден'},
                        status=status.HTTP_404_NOT_FOUND)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny,]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = [AllowAny,]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,]
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        return RecipeSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated,]
    )
    def favorite(self, request, pk=None):
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

    def add_recipe(self, serializer_cl, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {'recipe': recipe.id, 'user': request.user.id}
        serializer = serializer_cl(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED)

    def delete_recipe(self, model, user, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': 'Рецепт не найден!'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated,]
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self.add_recipe(ShoppingListtSerializer, request, pk)
        return self.delete_recipe(ShoppingList, request.user, pk)
