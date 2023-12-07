from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters

from recipes.models import Ingredient

User = get_user_model()

class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredient
        fields = ('name',)
