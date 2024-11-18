from django.contrib.auth.models import AbstractUser
from django.db import models
from users.validators import validate_username


class User(AbstractUser):
    """Кастомная модель пользователя."""
    class Role(models.TextChoices):
        USER = 'user', 'Пользователь'
        ADMIN = 'admin', 'Администратор'

    email = models.EmailField(max_length=250, unique=True,
                              blank=False, null=False)
    username = models.CharField(max_length=150, unique=True, blank=False,
                                null=False, validators=[validate_username])
    first_name = models.CharField(max_length=150, blank=False, null=False)
    last_name = models.CharField(max_length=150, blank=False, null=False)
    password = models.CharField(max_length=150, blank=False, null=False)
    role = models.CharField(max_length=150, choices=Role.choices,
                            default=Role.USER)
    avatar = models.ImageField(upload_to='avatars/image', blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    """Модель подписок."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='follower')
    following = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='following')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
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
