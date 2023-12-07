from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action

from .serializers import (FollowSerializer, TagSerializer,
                          IngredientSerializer, RecipeSerializer,
                          RecipeGetSerializer, FavoriteListSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer)
from users.models import Follow
from recipes.models import Tag, Ingredient, Recipe, Best, ShopCart, IngredientRecipe
from .filters import IngredientFilter

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
    """ Вьюха для работы с рецептами """

    queryset = Recipe.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete',)
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeGetSerializer
        elif self.action == 'favorite':
            return FavoriteListSerializer
        elif self.action == 'shopping_cart':
            return ShoppingCartSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=('post', 'delete',),
        detail=True,
        serializer_class=FavoriteListSerializer,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            response_data = serializer.save(id=pk)
            return Response(
                {'message': 'Рецепт добавлен в избранное.',
                 'data': response_data},
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            get_object_or_404(
                Best, user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)).delete()
            return Response(
                {'Рецепт удален из избранного'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        methods=('post', 'delete',),
        detail=True,
        serializer_class=ShoppingCartSerializer,
        permission_classes=(permissions.IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        if self.request.method == 'POST':
            serializer = self.get_serializer(
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            response_data = serializer.save(id=pk)
            return Response(
                {'message': 'Рецепт добавлен в список',
                 'data': response_data}, status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            get_object_or_404(
                ShopCart, user=self.request.user,
                recipe=get_object_or_404(Recipe, pk=pk)).delete()
            return Response(
                {'Рецепт удален из списка'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(permissions.IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        '''Скачать список покупок.'''

        shopping_cart = ShopCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_list = IngredientRecipe.objects.filter(
            recipe__in=recipes
        ).values(
            'ingredient'
        ).annotate(
            amount=Sum('amount')
        )
        buy_list_text = 'Foodgram\nСписок покупок:\n'
        for item in buy_list:
            ingredient = Ingredient.objects.get(pk=item['ingredient'])
            amount = item['amount']
            buy_list_text += (
                f'{ingredient.name}, {amount} '
                f'{ingredient.measurement_unit}\n'
            )
        response = HttpResponse(buy_list_text, content_type="text/plain")
        response['Content-Disposition'] = (
            'attachment; filename=shopping-list.txt'
        )
        return response