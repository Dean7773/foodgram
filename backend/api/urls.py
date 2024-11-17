from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (RecipeViewSet, TagViewSet, UserViewSet,
                       IngredientViewSet, UserSubscriptionsViewSet)

v1_router = DefaultRouter()
v1_router.register(r'recipes', RecipeViewSet, basename='recipes')
v1_router.register(r'tags', TagViewSet, basename='tags')
v1_router.register(r'ingredients', IngredientViewSet, basename='ingredients')


urlpatterns = [
    path('users/subscriptions/',
         UserSubscriptionsViewSet.as_view({'get': 'list'})),
    path('users/<int:user_id>/subscribe/',
         UserViewSet.as_view({'post': 'create',
                              'delete': 'destroy'})),
    path('', include(v1_router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
