from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.db import models

from .constants import (MAX_NAME_CHARACTERS, MAX_COLOR_CHARACTERS,
                        MAX_SLUG_CHARACTERS, MAX_UNIT_CHARACTERS,
                        MIN_COOKING_VALUE, COOKING_VALIDATION_MESSAGE,
                        MIN_INGREDIENT_VALUE, INGREDIENT_VALIDATION_MESSAGE)

User = get_user_model()


class Tag(models.Model):
    """ Модель тега """
    name = models.CharField('Название', max_length=MAX_NAME_CHARACTERS)
    color = models.CharField('Цвет', max_length=MAX_COLOR_CHARACTERS)
    slug = models.CharField('Слаг', max_length=MAX_SLUG_CHARACTERS, unique=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """ Модель ингредиента """
    name = models.CharField('Название', max_length=MAX_NAME_CHARACTERS)
    count = models.IntegerField()
    measurement_unit = models.CharField('Единицы измерения', max_length=MAX_UNIT_CHARACTERS)

    class Meta:
        ordering = ['id']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """ Модель рецепта """
    ingredients = models.ManyToManyField(Ingredient, through='IngredientRecipe', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, through='TagRecipe')
    image = models.ImageField('Фото', upload_to='recipe/images/',
                              null=True, default=None)
    name = models.CharField('Название', max_length=MAX_NAME_CHARACTERS)
    text = models.TextField('Описание', blank=True, null=True)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=(
            MinValueValidator(MIN_COOKING_VALUE,
                              message=COOKING_VALIDATION_MESSAGE)
        )
    )
    author = models.ForeignKey(User, related_name='recipes', on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_recipe')]

    def __str__(self):
        return self.name


class TagRecipe(models.Model):
    """ Промежуточная таблица между моделями Tag и Recipe """
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.tag} {self.recipe}'


class IngredientRecipe(models.Model):
    """ Промежуточная таблица между моделями Ingredient и Recipe """
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    count = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(MIN_INGREDIENT_VALUE,
                              message=INGREDIENT_VALIDATION_MESSAGE)
        )
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredients')]

    def __str__(self):
        return f'{self.ingredient} {self.count}'


class Best(models.Model):
    """ Избранные рецепты """
    author = models.ForeignKey(User, related_name='best', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [models.UniqueConstraint(
            fields=['author', 'recipe'],
            name='unique_best')]

    def __str__(self):
        return f'{self.recipe}'


class ShopCart(models.Model):
    """ Корзина для покупок """
    author = models.ForeignKey(User, related_name='shop_cart', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [models.UniqueConstraint(
            fields=['author', 'recipe'],
            name='unique_shop_cart')]

    def __str__(self):
        return f'{self.recipe}'
