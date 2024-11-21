from django.shortcuts import get_object_or_404, redirect
from rest_framework.views import APIView

from foodgram.models import Recipe


class ShortLinkViewSet(APIView):
    """Обработка коротких ссылок для рецептов."""
    def get(self, request, short_link=None):
        recipe = get_object_or_404(Recipe, uniq_code=short_link)
        full_url = request.build_absolute_uri(f'/recipes/{recipe.id}')
        return redirect(full_url)
