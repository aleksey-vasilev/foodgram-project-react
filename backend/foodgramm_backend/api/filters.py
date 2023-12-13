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
    is_favorited = filters.CharFilter(method='get_favorited')
    is_in_shopping_cart = filters.CharFilter(method='get_shop_cart')

    class Meta:
        model = Recipe
        fields = ('author',)

    def get_favorited(self, queryset, name, value):
        user = self.request.user
        if int(value) and user.is_authenticated:
            return queryset.filter(favorited__user=user)
        return queryset


    def get_shop_cart(self, queryset, name, value):
        user = self.request.user
        if int(value) and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset
