import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """Валидатор для проверки имени пользователя."""
    if not re.match(r'^[\w.@+-]+$', value):
        raise ValidationError('Имя содержит недопустимые символы.')
