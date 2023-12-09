import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .constants import (DULICATE_FOLLOW_ERROR, SELF_FOLLOW_ERROR)
from .mixins import UsernameValidatorMixin, RecipeValidatorMixin
from recipes.models import (Tag, Ingredient, Recipe,
                            IngredientRecipe, TagRecipe)
from users.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """ Описание поля для кодорования изображения в Base64 """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')  
            ext = format.split('/')[-1]  
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserSerializer(UsernameValidatorMixin, serializers.ModelSerializer):
    """
    Сериализатор для кастомной модели пользователя.
    Используется Djoser'ом для обработки стандартных эндпоинтов.
    """
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'password', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True},
                        'is_subscribed': {'read_only': True}}

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request.user.is_anonymous:
            return Follow.objects.filter(user=request.user, author=obj).exists()
        return False


class SubscriptionSerializer(UserSerializer):
    """ Сериализатор для получения списка подписок пользователя """
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
        if recipes_limit:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return RecipeLimitedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор для обработки подписки пользователя на автора"""
    class Meta:
        model = Follow
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(queryset=Follow.objects.all(),
                                    fields=('user', 'author'),
                                    message=DULICATE_FOLLOW_ERROR)
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(SELF_FOLLOW_ERROR)
        return data


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для тегов """
    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка ингредиентов """
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientModifySerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения ингредиентов """
    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientRetriveSerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения ингредиентов """
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_name(self, obj):
        return obj.ingredient.name


class RecipeModifySerializer(RecipeValidatorMixin, serializers.ModelSerializer):
    """ Сериализатор для изменения рецептов """
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()
    ingredients = IngredientModifySerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'
        read_only_fields = ('author',)

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            TagRecipe.objects.create(tag=tag, recipe=recipe)
        for ingredient in ingredients:
            IngredientRecipe.objects.create(ingredient_id=ingredient.get('id'),
                                            amount=ingredient.get('amount'),
                                            recipe=recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            for ingredient in ingredients:
                IngredientRecipe.objects.create(
                    ingredient_id=ingredient.get('id'),
                    amount=ingredient.get('amount'),
                    recipe=instance
                    )
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            for tag in tags:
                TagRecipe.objects.create(tag=tag, recipe=instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeRetriveSerializer(instance, context={
            'request': self.context.get('request')},).data


class RecipeRetriveSerializer(serializers.ModelSerializer):
    """ Сериализатор для чтения рецептов """
    image = Base64ImageField()
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True,
                            default=serializers.CurrentUserDefault())
    ingredients = IngredientRetriveSerializer(many=True, source='ingredientrecipe')
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, recipe):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.best.filter(recipe=recipe).exists()
        return False

    def get_is_in_shopping_cart(self, recipe):
        user = self.context.get('request').user
        if user.is_authenticated:
            return user.shop_cart.filter(recipe=recipe).exists()
        return False


class RecipeLimitedSerializer(serializers.ModelSerializer):
    """ Сериализатор для чтения рецептов находящихся в корзине и избранном """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
