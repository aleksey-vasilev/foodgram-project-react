from drf_extra_fields.fields import Base64ImageField as DRF_Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .constants import (NO_INGREDIENTS_ERROR, NO_TAGS_ERROR,
                        NOT_EXIST_INGREDIENT_ERROR, AMOUNT_LT_ONE_ERROR,
                        DUPLICATE_INGREDIENT_ERROR, DUPLICATE_TAG_ERROR,
                        DULICATE_FOLLOW_ERROR, SELF_FOLLOW_ERROR,
                        NO_AUTH_USERS_ME)
from recipes.models import (Tag, Ingredient, Recipe,
                            IngredientRecipe, TagRecipe, User)
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
                  'email', 'password', 'is_subscribed')
        extra_kwargs = {'password': {'write_only': True},
                        'is_subscribed': {'read_only': True}}

    def get_is_subscribed(self, author):
        request = self.context['request']
        return (request and request.user.is_authenticated
                and request.user.follower.filter(author=author).exists())


class SubscriptionSerializer(UserSerializer):
    """ Сериализатор для получения списка подписок пользователя. """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField()

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
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
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

    id = serializers.IntegerField(write_only=True)
    amount = serializers.IntegerField(write_only=True)

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')

    def validate_amount(self, amount):
        if int(amount) < 1:
            raise serializers.ValidationError(AMOUNT_LT_ONE_ERROR)
        return amount
    
    def validate_id(self, id):
        if not Ingredient.objects.filter(id=id).exists():
            raise serializers.ValidationError(NOT_EXIST_INGREDIENT_ERROR)
        return id


class IngredientRetriveSerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения ингредиентов. """

    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def get_name(self, obj):
        return obj.ingredient.name


class RecipeModifySerializer(serializers.ModelSerializer):
    """ Сериализатор для изменения рецептов. """

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    image = Base64ImageField()
    ingredients = IngredientModifySerializer(many=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)
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
                    recipe=instance)
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.clear()
            for tag in tags:
                TagRecipe.objects.create(tag=tag, recipe=instance)
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
        all_tags = [tag for tag in tags]
        if len(all_tags) != len(set(all_tags)):
            raise serializers.ValidationError(DUPLICATE_TAG_ERROR)
        return data


class RecipeRetriveSerializer(serializers.ModelSerializer):
    """ Сериализатор для чтения рецептов. """

    image = Base64ImageField()
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True,
                            default=serializers.CurrentUserDefault())
    ingredients = IngredientRetriveSerializer(many=True,
                                              source='ingredientrecipe')
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

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
    """ Сериализатор для чтения рецептов находящихся в корзине и избранном. """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
