from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import serializers

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
            return Follow.objects.filter(user=user, following=obj).exists()
        return False


class FollowSerializer(serializers.Serializer):
    def validate(self, data):
        user = self.context.get('request').user
        author = get_object_or_404(User, pk=self.context.get('view').kwargs.get('author_id'))
        if user == author:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Такая подписка уже есть'
            )
        return data

    def create(self, validated_data):
        user = self.context.get('request').user
        author = get_object_or_404(User, pk=self.context.get('view').kwargs.get('author_id'))
        Follow.objects.create(user=user, author=author)
        serializer = UserSerializer(
            author, context={'request': self.context.get('request')}
        )
        return serializer.data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag

class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(many=True,
                                              queryset=Tag.objects.all())
    #ingredients = AddIngredientRecipeSerializer(many=True)
    #image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            #'ingredients',
            'tags',
            #'image',
            'name',
            'text',
            'cooking_time',
        )

    def add_ingredients(self, recipe, ingredients_data):
        ingredients = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['ingredient']['id']
            amount = ingredient_data['amount']
            ingredient = Ingredient.objects.get(id=ingredient_id)
            if IngredientRecipe.objects.filter(
                    recipe=recipe, ingredient=ingredient_id).exists():
                amount += F('amount')
            recipe_ingredient = IngredientRecipe(
                recipe=recipe, ingredient=ingredient, amount=amount
            )
            ingredients.append(recipe_ingredient)
        IngredientRecipe.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.add_ingredients(recipe, ingredients_data)
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags')
        IngredientRecipe.objects.filter(recipe=instance).delete()
        self.add_ingredients(instance, ingredients)
        instance.tags.set(tags)
        return super().update(instance, validated_data)

class RecipeIngredientSerializer(serializers.ModelSerializer):
    '''Добавление ингредиентов в рецепт.'''

    id = serializers.IntegerField(write_only=True)
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurements_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        '''Проверяем, что количество ингредиента больше 0.'''

        if value <= 0:
            raise ValidationError(
                'Количество ингредиента должно быть больше 0'
            )
        return value


class RecipeGetSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = TagSerializer(
        many=True,
        read_only=True
    )
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    #image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
      #      'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                return obj.favorites.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request:
            user = request.user
            if user.is_authenticated:
                shopping_list = ShopCart.objects.filter(
                    user=user, recipe=obj
                )
                return shopping_list.exists()
        return False

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
        serializer = RecipeSerializer(recipe)
        return serializer.data

class ShoppingCartSerializer(serializers.Serializer):
    def create(self, validated_data):
        recipe = get_object_or_404(Recipe, pk=validated_data['id'])
        ShopCart.objects.create(
            user=self.context['request'].user,
            recipe=recipe
        )
        serializer = RecipeSerializer(recipe)
        return serializer.data