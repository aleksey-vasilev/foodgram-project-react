import django_filters as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """ Фильтр по отдельным ингредиентам. """

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """ Фильтр рецептов по тегам и автору. """

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all())
    is_favorited = filters.CharFilter(field_name='is_favorited')
    is_in_shopping_cart = filters.CharFilter(
        field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author',)
