from django.contrib.auth import get_user_model
from django.db.models.expressions import Exists, OuterRef, Value
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .serializers import (FollowSerializer, TagSerializer,
                          IngredientSerializer, RecipeGetSerializer,
                          RecipeModifySerializer, SubscriptionSerializer)
from users.models import Follow
from recipes.models import (Tag, Ingredient, Recipe,
                            Best, ShopCart)
from .filters import IngredientFilter, RecipeFilter

User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    """ Получение тегов """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    http_method_names = ('get',)


class UserSubscriptionViewSet(mixins.ListModelMixin,
                              viewsets.GenericViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserSubscribeViewSet(APIView):
    def post(self, request, author_id):
        user = get_object_or_404(User, username=request.user)
        author = get_object_or_404(User, id=author_id)
        serializer = FollowSerializer(
            data={'user': user.id, 'author': author_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscriptionSerializer(
            author, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = self.request.user
        if Follow.objects.filter(author=author, user=user).exists():
            Follow.objects.get(author=author).delete()
            return Response('Успешная отписка',
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Объект не найден'},
                        status=status.HTTP_404_NOT_FOUND)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Получение списка ингридиентов """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ Рецепты """
    queryset = Recipe.objects.all()
    #filterset_class = RecipeFilter
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGetSerializer
        return RecipeModifySerializer

    def get_queryset(self):
        return Recipe.objects.all()
        '''
        return Recipe.objects.annotate(
            is_favorited=Exists(
                Best.objects.filter(
                    user=self.request.user, recipe=OuterRef('id'))),
            is_in_shopping_cart=Exists(
                ShopCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef('id')))
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        ) if self.request.user.is_authenticated else Recipe.objects.annotate(
            is_in_shopping_cart=Value(False),
            is_favorited=Value(False),
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe')
        '''

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        pass
