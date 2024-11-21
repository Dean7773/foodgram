from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from users.constant import (MAX_EMAIL, MAX_USERNAME, MAX_PASSWORD_LENGHT,
                            MAX_FIRST_NAME, MAX_LAST_NAME)


class User(AbstractUser):
    """Кастомная модель пользователя."""
    email = models.EmailField(
        max_length=MAX_EMAIL,
        unique=True,
        verbose_name='эл.почта'
    )
    username = models.CharField(
        max_length=MAX_USERNAME,
        unique=True,
        validators=(UnicodeUsernameValidator(), ),
        verbose_name='имя пользователя'
    )
    first_name = models.CharField(
        max_length=MAX_FIRST_NAME,
        verbose_name='имя'
    )
    last_name = models.CharField(
        max_length=MAX_LAST_NAME,
        verbose_name='фамилия'
    )
    password = models.CharField(
        max_length=MAX_PASSWORD_LENGHT,
        verbose_name='пароль'
    )
    avatar = models.ImageField(
        upload_to='avatars/image', blank=True,
        verbose_name='аватар'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('email', )
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    """Модель подписок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='подписчик',
        related_name='follower'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
        related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_following'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('following')),
                name='following_yourself'
            )
        ]
        verbose_name = 'Подписки'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} подписан на {self.following.username}'
