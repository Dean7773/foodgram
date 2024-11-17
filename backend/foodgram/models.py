from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов, которые будут использоваться в рецептах."""
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Теги."""
    name = models.CharField(max_length=20)
    slug = models.SlugField(unique=True, max_length=50)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='recipes')
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='recipes/image', blank=True)
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', related_name='recipes')
    tags = models.ManyToManyField(Tag, related_name='recipes', blank=True)
    cooking_time = models.PositiveSmallIntegerField()
    pub_date = models.DateTimeField('Дата создания рецепта', auto_now_add=True)

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи ингредиентов и рецептов."""
    """Добавляет поля количества и еденицы измерения ингредиента."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20)

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorites(models.Model):
    """Модель избранных рецептов."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='favorites')
    favorites = models.ForeignKey(Recipe, on_delete=models.SET_NULL,
                                  null=True, related_name='favorites')

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'favorites')

    def __str__(self):
        return self.favorites


class ShoppingList(models.Model):
    """Модель списка покупок."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='shoppinglist')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return (f'{self.user.username} добавил '
                f'рецепт {self.recipe.title} в список покупок.')
