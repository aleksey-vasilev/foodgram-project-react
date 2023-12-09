from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (FollowSerializer, TagSerializer,
                          IngredientSerializer, RecipeRetriveSerializer,
                          RecipeModifySerializer, SubscriptionSerializer,
                          RecipeLimitedSerializer)
from recipes.models import (Tag, Ingredient, Recipe, Best, ShopCart)
from users.models import Follow

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


class UserSubscribeAPIView(APIView):
    def post(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = self.request.user
        serializer = FollowSerializer(
            data={'user': user.id, 'author': author_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscriptionSerializer(author, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = self.request.user
        if Follow.objects.filter(author=author, user=user).exists():
            Follow.objects.get(author=author).delete()
            return Response('Успешная отписка',
                            status=status.HTTP_204_NO_CONTENT)
        return Response('Объект не найден', status=status.HTTP_404_NOT_FOUND)


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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            is_in_shopping_cart = self.request.query_params.get('is_in_shopping_cart')
            if is_in_shopping_cart:
                return self.queryset.filter(in_shopping_cart__user=self.request.user)
            is_favorited = self.request.query_params.get('is_favorited')
            if is_favorited:
                return self.queryset.filter(favorited__user=self.request.user)
            return self.queryset
        return self.queryset


    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeRetriveSerializer
        return RecipeModifySerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk):
        if request.method == 'POST':
            if not Recipe.objects.all().filter(id=pk):
                return Response('Такого рецепта нет', status=status.HTTP_400_BAD_REQUEST)
            if Best.objects.filter(user=request.user, recipe__id=pk).exists():
                return Response('Уже в избранном', status=status.HTTP_400_BAD_REQUEST)
            recipe = get_object_or_404(Recipe, id=pk)
            Best.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeLimitedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            Best.objects.filter(user=request.user, recipe__id=pk).delete()
            return Response('Рецепт удален из избранного', status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            if not Recipe.objects.all().filter(id=pk):
                return Response('Такого рецепта нет', status=status.HTTP_400_BAD_REQUEST)
            if ShopCart.objects.filter(user=request.user,
                                       recipe__id=pk).exists():
                return Response('Уже в корзине!', status=status.HTTP_400_BAD_REQUEST)
            recipe = get_object_or_404(Recipe, id=pk)
            ShopCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeLimitedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            ShopCart.objects.filter(user=request.user, recipe__id=pk).delete()
            return Response('Рецепт удален из корзины', status=status.HTTP_204_NO_CONTENT)
