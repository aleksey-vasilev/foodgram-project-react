import django_filters as filters

from recipes.models import Ingredient, Recipe


class IngredientFilter(filters.FilterSet):
    """ Фильтр по отдельным ингредиентам"""
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """ Фильтр рецептов по тегам и автору """
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author',)
