import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from foodgram import constant

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов, которые будут использоваться в рецептах."""
    name = models.CharField(
        verbose_name='ингредиент',
        max_length=constant.MAX_NAME_INGREDIENT
    )
    measurement_unit = models.CharField(
        verbose_name='измеряемая величина',
        max_length=constant.MAX_MEASUREMENT
    )

    class Meta:
        ordering = ['-name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_name_measurement_unit')
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Теги."""
    name = models.CharField(
        verbose_name='тег',
        max_length=constant.MAX_TAG_NAME,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='слаг',
        max_length=constant.MAX_TAG_SLUG,
        unique=True
    )

    class Meta:
        ordering = ['-name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(
        User,
        verbose_name='автор',
        on_delete=models.CASCADE,
    )
    name = models.CharField(
        verbose_name='название рецепта',
        max_length=constant.MAX_NAME_RECIPE
    )
    image = models.ImageField(
        verbose_name='картинка',
        upload_to='recipes/image',
        blank=True
    )
    text = models.TextField(verbose_name='описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='ингредиенты',
        through='RecipeIngredient',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='теги',
        blank=True
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='время приготовления',
        validators=[
            MinValueValidator(constant.MIN_COOKING_TIME,
                              'Минимальное время приготовления - 1'),
            MaxValueValidator(constant.MAX_COOKING_TIME,
                              'Максимальное время приготовления - 32767')
        ],
    )
    pub_date = models.DateTimeField(
        verbose_name='дата создания рецепта',
        auto_now_add=True
    )
    uniq_code = models.CharField(
        verbose_name='код для короткой ссылки',
        max_length=constant.MAX_UNIQ_CODE,
        unique=True,
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def generate_unique_code(self):
        characters = string.ascii_letters + string.digits
        while True:
            code = ''.join(random.choices(characters,
                                          k=constant.MAX_UNIQ_CODE))
            if not Recipe.objects.filter(uniq_code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if not self.uniq_code:
            self.uniq_code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи ингредиентов и рецептов."""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='количество ингредиента',
        validators=[
            MinValueValidator(constant.MIN_AMOUNT_INGREDIENT,
                              'Минимальное количество - 1'),
            MaxValueValidator(constant.MAX_AMOUNT_INGREDIENT,
                              'Максимальное количество - 32767')
        ],
    )

    class Meta:
        ordering = ['-recipe__pub_date']
        default_related_name = 'recipeingredient'
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'{self.amount} {self.ingredient} в {self.recipe}'


class Favorites(models.Model):
    """Модель избранных рецептов."""
    user = models.ForeignKey(
        User,
        verbose_name='пользователь',
        on_delete=models.CASCADE
    )
    favorites = models.ForeignKey(
        Recipe,
        verbose_name='рецепт',
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        ordering = ['-favorites__pub_date']
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(fields=['user', 'favorites'],
                                    name='unique_user_favorite')
        ]

    def __str__(self):
        return self.favorites


class ShoppingList(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(
        User,
        verbose_name='пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-recipe__pub_date']
        default_related_name = 'carts'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_user_recipe')
        ]

    def __str__(self):
        return (f'{self.user.username} добавил '
                f'рецепт {self.recipe.name} в список покупок.')
