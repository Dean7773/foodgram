from django.urls import path

from foodgram.views import ShortLinkViewSet

urlpatterns = [
    path('s/<str:short_link>/',
         ShortLinkViewSet.as_view(), name='short-link-redirect'),
]
