from rest_framework import serializers

from .constants import (NO_INGREDIENTS_ERROR, NO_TAGS_ERROR, NOT_EXIST_INGREDIENT_ERROR,
                        AMOUNT_LT_ONE_ERROR, DUPLICATE_INGREDIENT_ERROR, DUPLICATE_TAG_ERROR)
from recipes.models import Tag, Ingredient
from users.validators import validator_username


class UsernameValidatorMixin:
    """ Валидация имени пользователя """
    def validate_username(self, value):
        return validator_username(value)


class RecipeValidatorMixin:
    """ Валидация рецепта """
    def validate(self, data):
        if not data.get('ingredients'):
            raise serializers.ValidationError(NO_INGREDIENTS_ERROR)
        if not data.get('tags'):
            raise serializers.ValidationError(NO_TAGS_ERROR)
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(NO_INGREDIENTS_ERROR)
        all_ingredients = []
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError(NOT_EXIST_INGREDIENT_ERROR)
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(AMOUNT_LT_ONE_ERROR)
            if ingredient in all_ingredients:
                raise serializers.ValidationError(DUPLICATE_INGREDIENT_ERROR)
            all_ingredients.append(ingredient)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(NO_TAGS_ERROR)
        all_tags = []
        for tag in tags:
            if tag in all_tags:
                raise serializers.ValidationError(DUPLICATE_TAG_ERROR)
            all_tags.append(tag)
        return tags
