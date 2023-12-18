from colorfield.fields import ColorField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from .constants import (MAX_NAME_CHARACTERS, MAX_COLOR_CHARACTERS,
                        MAX_SLUG_CHARACTERS, MIN_COOKING_VALUE,
                        COOKING_VALIDATION_MESSAGE, MIN_INGREDIENT_VALUE,
                        INGREDIENT_VALIDATION_MESSAGE, MAX_SMALL_INTEGER)

from users.models import User


class Tag(models.Model):
    """ Модель тега. """

    name = models.CharField('Название', max_length=MAX_NAME_CHARACTERS)
    color = ColorField('Цвет', max_length=MAX_COLOR_CHARACTERS)
    slug = models.CharField('Слаг', max_length=MAX_SLUG_CHARACTERS,
                            unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """ Модель ингредиента. """

    name = models.CharField('Название', max_length=MAX_NAME_CHARACTERS)
    measurement_unit = models.CharField('Единицы измерения',
                                        max_length=MAX_SMALL_INTEGER)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_ingredient'),)

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):
    def annotated(self, user):
        is_favorited = Best.objects.all().filter(
            recipe__pk=models.OuterRef('pk'), user=user)
        is_in_shopping_cart = ShopCart.objects.all().filter(
            recipe__pk=models.OuterRef('pk'), user=user)
        return self.annotate(
            is_in_shopping_cart=models.Exists(is_in_shopping_cart),
            is_favorited=models.Exists(is_favorited))


class Recipe(models.Model):
    """ Модель рецепта. """

    objects = RecipeQuerySet.as_manager()

    ingredients = models.ManyToManyField(Ingredient, related_name='recipes',
                                         through='IngredientRecipe')
    tags = models.ManyToManyField(Tag, related_name='recipes')
    image = models.ImageField('Фото', upload_to='recipe/images/',
                              null=True, default=None)
    name = models.CharField('Название', max_length=MAX_NAME_CHARACTERS)
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(MIN_COOKING_VALUE,
                              message=COOKING_VALIDATION_MESSAGE),
            MaxValueValidator(MAX_SMALL_INTEGER,
                              message=COOKING_VALIDATION_MESSAGE),
        ]
    )
    author = models.ForeignKey(User, related_name='recipes',
                               on_delete=models.CASCADE)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_recipe'),)

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """ Промежуточная таблица между моделями Ingredient и Recipe. """

    ingredient = models.ForeignKey(Ingredient, related_name='ingredientrecipe',
                                   on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='ingredientrecipe',
                               on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_VALUE,
                              message=INGREDIENT_VALIDATION_MESSAGE),
            MaxValueValidator(MAX_SMALL_INTEGER,
                              message=INGREDIENT_VALIDATION_MESSAGE),
        ]
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredients'),)

    def __str__(self):
        return f'{self.ingredient} {self.recipe}'


class ShopCartBestBaseModel(models.Model):
    """ Базовый класс для корзины и избранного. """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)

    class Meta:
        abstract = True
        constraints = (models.UniqueConstraint(
            fields=('user', 'recipe'),
            name='unique_%(class)s'),)

    def __str__(self):
        return f'{self.recipe} добавлен в {self.__class__.__name__}'


class Best(ShopCartBestBaseModel):
    """ Избранные рецепты. """

    class Meta(ShopCartBestBaseModel.Meta):
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        default_related_name = 'best_set'


class ShopCart(ShopCartBestBaseModel):
    """ Корзина для списка покупок. """

    class Meta(ShopCartBestBaseModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopcart_set'
