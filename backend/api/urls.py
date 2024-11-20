from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                       UserSubscriptionsViewSet, UserViewSet)

v1_router = DefaultRouter()
v1_router.register(r'recipes', RecipeViewSet, basename='recipes')
v1_router.register(r'ingredients', IngredientViewSet, basename='ingredients')
v1_router.register(r'tags', TagViewSet, basename='tags')
v1_router.register(r'subscriptions', UserSubscriptionsViewSet,
                   basename='subscriptions')


urlpatterns = [
    path('users/subscriptions/',
         UserSubscriptionsViewSet.as_view({'get': 'list'})),
    path('users/<int:user_id>/subscribe/',
         UserViewSet.as_view({'post': 'create',
                              'delete': 'destroy'})),
    path('users/me/', UserViewSet.as_view({'get': 'me'})),
    path('users/me/avatar/',
         UserViewSet.as_view({'put': 'upload_avatar',
                              'delete': 'delete_avatar'}), name='avatar'),
    path('', include(v1_router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
