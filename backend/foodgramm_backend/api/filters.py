from django.contrib.auth import get_user_model
import django_filters as filters

from recipes.models import Ingredient, Recipe

User = get_user_model()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    is_in_shopping_cart = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget())
    is_favorited = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget())
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')
