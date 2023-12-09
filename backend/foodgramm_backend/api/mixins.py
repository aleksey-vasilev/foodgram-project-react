from rest_framework import serializers

from recipes.models import Tag, Ingredient
from users.validators import validator_username
class UsernameValidatorMixin:
    def validate_username(self, value):
        return validator_username(value)


class RecipeValidatorMixin:
    def validate(self, data):
        if not data.get('ingredients'):
            raise serializers.ValidationError('Ни один ингридиент не указан')
        if not data.get('tags'):
            raise serializers.ValidationError('Ни один тег не указан')
        return data

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Нет ингредиентов')
        all_ingredients = []
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError('Несуществующий ингредиент')
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError('Количество не может быть 0')
            if ingredient in all_ingredients:
                raise serializers.ValidationError('Введен повторяющийся ингредиент')
            all_ingredients.append(ingredient)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Нет тегов')
        all_tags = []
        for tag in tags:
            if tag in all_tags:
                raise serializers.ValidationError('Введен повторяющийся тег')
            all_tags.append(tag)
        return tags
