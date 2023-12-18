from django.db import transaction
from drf_extra_fields.fields import Base64ImageField as DRF_Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .constants import (NO_INGREDIENTS_ERROR, NO_TAGS_ERROR,
                        NO_IMAGE_FIELD, SELF_FOLLOW_ERROR,
                        DUPLICATE_INGREDIENT_ERROR, DUPLICATE_TAG_ERROR,
                        DULICATE_FOLLOW_ERROR, ALREADY_IN,
                        AMOUNT_MAX_VALUE, AMOUNT_MIN_VALUE,
                        MAX_VALUE_ERROR, MIN_VALUE_ERROR)
from recipes.models import (Tag, Ingredient, Recipe,
                            IngredientRecipe, User,
                            ShopCart, Best)
from users.models import Follow


class Base64ImageField(DRF_Base64ImageField):
    """ Описание поля для кодорования изображения в Base64. """

    def to_representation(self, image):
        return image.url


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для кастомной модели пользователя.
    Используется Djoser'ом для обработки стандартных эндпоинтов.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'is_subscribed')

    def get_is_subscribed(self, author):
        request = self.context['request']
        return (request and request.user.is_authenticated
                and request.user.follower.filter(author=author).exists())


class SubscriptionSerializer(UserSerializer):
    """ Сериализатор для получения списка подписок пользователя. """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')
        read_only_fields = ('email', 'username', 'first_name', 'last_name',
                            'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context['request']
        recipes_limit = None
        if request:
            recipes_limit = request.query_params.get('recipes_limit')
            recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        return RecipeLimitedSerializer(recipes, many=True).data


class FollowSerializer(serializers.ModelSerializer):
    """ Сериализатор для обработки подписки пользователя на автора. """

    class Meta:
        model = Follow
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(queryset=Follow.objects.all(),
                                    fields=('user', 'author'),
                                    message=DULICATE_FOLLOW_ERROR)
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(SELF_FOLLOW_ERROR)
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance.author,
                                      context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    """ Сериализатор для тегов. """

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    """ Сериализатор для списка ингредиентов. """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientModifySerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения ингредиентов. """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        write_only=True,
        max_value=AMOUNT_MAX_VALUE,
        min_value=AMOUNT_MIN_VALUE,
        error_messages={'max_value': MAX_VALUE_ERROR.format(AMOUNT_MAX_VALUE),
                        'min_value': MIN_VALUE_ERROR.format(AMOUNT_MIN_VALUE)})

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')


class IngredientRetriveSerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения ингредиентов. """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeModifySerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения рецептов. """

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()
    ingredients = IngredientModifySerializer(many=True)
    cooking_time = serializers.IntegerField(
        write_only=True,
        max_value=AMOUNT_MAX_VALUE,
        min_value=AMOUNT_MIN_VALUE,
        error_messages={'max_value': MAX_VALUE_ERROR.format(AMOUNT_MAX_VALUE),
                        'min_value': MIN_VALUE_ERROR.format(AMOUNT_MIN_VALUE)})

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
        read_only_fields = ('author',)

    @staticmethod
    def create_ingredientrecipe(ingredients, recipe):
        IngredientRecipe.objects.bulk_create(
            IngredientRecipe(ingredient=ingredient.get('id'),
                             amount=ingredient.get('amount'),
                             recipe=recipe)
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredientrecipe(ingredients, recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.create_ingredientrecipe(ingredients, instance)
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeRetriveSerializer(instance, context=self.context).data

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(NO_INGREDIENTS_ERROR)
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(NO_TAGS_ERROR)
        all_ingredients = [ingredient.get('id') for ingredient in ingredients]
        if len(all_ingredients) != len(set(all_ingredients)):
            raise serializers.ValidationError(DUPLICATE_INGREDIENT_ERROR)
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(DUPLICATE_TAG_ERROR)
        return data

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError(NO_IMAGE_FIELD)
        return image


class RecipeRetriveSerializer(serializers.ModelSerializer):
    """ Сериализатор для чтения рецептов. """

    image = Base64ImageField()
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True,
                            default=serializers.CurrentUserDefault())
    ingredients = IngredientRetriveSerializer(many=True,
                                              source='ingredientrecipe')
    is_favorited = serializers.BooleanField(read_only=True, default=0)
    is_in_shopping_cart = serializers.BooleanField(read_only=True, default=0)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeLimitedSerializer(serializers.ModelSerializer):
    """ Сериализатор для чтения рецептов находящихся в корзине и избранном. """

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class BestShopCartSerializer(serializers.ModelSerializer):
    """ Родитель для сериалайзеров Best и ShopCart. """

    def validate(self, data):
        if self.Meta.model.objects.all().filter(**data).exists():
            raise serializers.ValidationError(ALREADY_IN)
        return data

    def to_representation(self, instance):
        return RecipeLimitedSerializer(
            instance.recipe,
            context=self.context).data

    class Meta:
        fields = ('recipe', 'user')


class ShopCartSerializer(BestShopCartSerializer):
    """ Сериализатор для рецептов находящихся в корзине """

    class Meta(BestShopCartSerializer.Meta):
        model = ShopCart


class BestSerializer(BestShopCartSerializer):
    """ Сериализатор для  рецептов находящихся в избранном. """

    class Meta(BestShopCartSerializer.Meta):
        model = Best
