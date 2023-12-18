from django.db.models import Sum
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from .constants import (SUCCESS_UNFOLLOW, FOLLOWING_NOT_FOUND,
                        RECIPE_NOT_FOUND)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (FollowSerializer, TagSerializer,
                          IngredientSerializer, RecipeRetriveSerializer,
                          RecipeModifySerializer, SubscriptionSerializer,
                          BestSerializer, ShopCartSerializer)
from recipes.models import (Tag, Ingredient, Recipe,
                            Best, ShopCart, IngredientRecipe,
                            User)
from users.models import Follow
from .prepare_pdf import prepare_pdf_buffer


class UserViewSet(DjoserUserViewSet):
    """ Работа с пользователями. """

    def get_permissions(self):
        if self.action == 'me':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=self.request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(page, many=True,
                                            context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('POST',),
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, id):
        user = self.request.user
        serializer = FollowSerializer(
            data={'user': user.id, 'author': id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        user = self.request.user
        follow = Follow.objects.filter(user=user, author_id=id)
        if follow.exists():
            follow.delete()
            return Response(SUCCESS_UNFOLLOW,
                            status=status.HTTP_204_NO_CONTENT)
        return Response(FOLLOWING_NOT_FOUND,
                        status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """ Получение тегов. """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    http_method_names = ('get',)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ Получение списка ингридиентов. """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ Вьюсет для работы с рецептами. """

    queryset = Recipe.objects.all().select_related(
        'author').prefetch_related('tags', 'ingredients')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.annotated(user)
        return self.queryset

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeRetriveSerializer
        return RecipeModifySerializer

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        shopping_list = IngredientRecipe.objects.filter(
            recipe__shopcart_set__user=request.user).values(
            'ingredient__name', 'ingredient__measurement_unit').order_by(
                'ingredient__name').annotate(amount=Sum('amount'))
        return FileResponse(prepare_pdf_buffer(shopping_list),
                            as_attachment=True,
                            filename='shop_cart.pdf',
                            status=status.HTTP_200_OK)

    @staticmethod
    def save_method(serializer, pk, request):
        context = {'request': request}
        data = {'user': request.user.id, 'recipe': pk}
        serialized = serializer(data=data, context=context)
        serialized.is_valid(raise_exception=True)
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_method(model, pk, request):
        recipe = model.objects.filter(user=request.user, recipe__id=pk)
        if not recipe.exists():
            return Response(RECIPE_NOT_FOUND,
                            status=status.HTTP_400_BAD_REQUEST)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=('POST',),
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self.save_method(ShopCartSerializer, pk, request)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_method(ShopCart, pk, request)

    @action(detail=True, methods=('POST',),
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk):
        return self.save_method(BestSerializer, pk, request)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_method(Best, pk, request)
