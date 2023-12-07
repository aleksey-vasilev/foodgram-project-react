from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import F
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .mixins import UsernameVilidatorMixin
from users.models import Follow
from recipes.models import Tag, Ingredient, Recipe, IngredientRecipe, Best, ShopCart

User = get_user_model()


class UserSerializer(UsernameVilidatorMixin, serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True},
                        'is_subscribed': {'read_only': True},
                        }

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Follow.objects.filter(user=user, author=obj).exists()
        return False


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = obj.recipes.all()[:int('recipes_limit')]
        return RecipeGetSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписаться себя'
            )
        return data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = (
            'id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError(
                'Количество должно быть больше 0'
            )
        return value


class RecipePostSerializer(serializers.ModelSerializer):
    image = Base64ImageField(
        max_length=None,
        use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all())
    ingredients = IngredientSerializer(
        many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(
                Ingredient, id=items['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Такой ингридиент уже есть')
            ingredient_list.append(ingredient)
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Нужен тег')
        for tag_name in tags:
            if not Tag.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f'Тэга {tag_name} нет')
        return data

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время приготовления больше 1 минуты')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Количество ингредиентов не может быть 0')
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество не может быть 0')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'), )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeGetSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class RecipeGetSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(
        many=True,
        read_only=True)
    author = UserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source='recipe')
    is_favorited = serializers.BooleanField(
        read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'


class FavoriteListSerializer(serializers.Serializer):
    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, pk=validated_data['id'])
        try:
            Best.objects.create(
                user=self.context['request'].user, recipe=recipe
            )
        except IntegrityError:
            raise serializers.ValidationError(
                'Уже в избранном'
            )
        serializer = RecipeGetSerializer(recipe)
        return serializer.data


class ShoppingCartSerializer(serializers.Serializer):
    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, pk=validated_data['id'])
        ShopCart.objects.create(
            user=self.context['request'].user,
            recipe=recipe
        )
        serializer = RecipeGetSerializer(recipe)
        return serializer.data