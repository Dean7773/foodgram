from django.urls import path

from foodgram.views import ShortLinkViewSet

urlpatterns = [
    path('s/<str:short_link>/',
         ShortLinkViewSet.as_view({'get': 'short_link_redirect'}),
         name='short-link-redirect'),
]
