from django.contrib import admin
from django.urls import include, path

from api.views import ShortLinkViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_link>/',
         ShortLinkViewSet.as_view({'get': 'short_link_redirect'}),
         name='short_link_redirect'),
]
