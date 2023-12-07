from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .mixins import UsernameVilidatorMixin
from users.models import Follow
from recipes.models import Tag

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


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='author.email', read_only=True)
    id = serializers.IntegerField(source='author.id', read_only=True)
    username = serializers.CharField(source='author.username', read_only=True)
    first_name = serializers.CharField(source='author.first_name', read_only=True)
    last_name = serializers.CharField(source='author.last_name', read_only=True)
    #recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    #recipes_count = serializers.ReadOnlyField(
    #    source='author.recipe.count')

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',) #'recipes', 'recipes_count',)

    #def get_recipes(self, obj):
    #    recipes = obj.author.recipe.all()
    #    return SubscribeRecipeSerializer(
    #        recipes,
    #        many=True).data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if not user.is_anonymous:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False

class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'color', 'slug')
        model = Tag
