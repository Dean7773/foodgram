from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                       UserSubscriptionsViewSet, UserViewSet)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('tags', TagViewSet, basename='tags')
router.register('subscriptions', UserSubscriptionsViewSet,
                basename='subscriptions')


urlpatterns = [
    path('users/subscriptions/',
         UserSubscriptionsViewSet.as_view({'get': 'list'})),
    path('users/me/', UserViewSet.as_view({'get': 'me'})),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
