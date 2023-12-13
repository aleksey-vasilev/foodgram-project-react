import io
import os

from django.http import FileResponse
from django.conf import settings
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from reportlab.pdfgen import canvas
from reportlab.lib.colors import red
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import (SUCCESS_UNFOLLOW, FOLLOWING_NOT_FOUND,
                        RECIPE_NOT_FOUND, ALREADY_IN_BEST,
                        RECIPE_NOT_IN_BEST, SUCCESS_REMOVE_FROM_BEST,
                        ALREADY_IN_CART, SUCCESS_REMOVE_FROM_CART,
                        RECIPE_NOT_IN_CART, SHOP_LIST_TITLE,
                        SHOP_LIST_HEAD, SHOP_LIST_ITEMS_PER_PAGE)
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (FollowSerializer, TagSerializer,
                          IngredientSerializer, RecipeRetriveSerializer,
                          RecipeModifySerializer, SubscriptionSerializer,
                          RecipeLimitedSerializer)
from recipes.models import (Tag, Ingredient, Recipe,
                            Best, ShopCart, IngredientRecipe)
from users.models import Follow

User = get_user_model()


class TagViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """ Получение тегов. """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    http_method_names = ('get',)


class UserSubscriptionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """ Просмотр списка подписок. """

    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return User.objects.filter(following__user=self.request.user)


class UserSubscribeAPIView(APIView):
    """ Подписка и отписка от автора. """

    def post(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = self.request.user
        serializer = FollowSerializer(
            data={'user': user.id, 'author': author_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscriptionSerializer(author,
                                            context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        user = self.request.user
        if Follow.objects.filter(author=author, user=user).exists():
            Follow.objects.get(author=author).delete()
            return Response(SUCCESS_UNFOLLOW,
                            status=status.HTTP_204_NO_CONTENT)
        return Response(FOLLOWING_NOT_FOUND,
                        status=status.HTTP_400_BAD_REQUEST)


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

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            is_in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart')
            if is_in_shopping_cart:
                return self.queryset.filter(
                    in_shopping_cart__user=self.request.user)
            is_favorited = self.request.query_params.get('is_favorited')
            if is_favorited:
                return self.queryset.filter(favorited__user=self.request.user)
        return self.queryset

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeRetriveSerializer
        return RecipeModifySerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _page_create(self, p, page):
        p.saveState()
        p.setStrokeColor(red)
        p.setLineWidth(5)
        p.line(66, 72, 66, p._pagesize[1] - 72)
        p.setFont('FreeSans', 24)
        p.drawString(108, p._pagesize[1] - 108, SHOP_LIST_TITLE)
        p.setFont('FreeSans', 12)
        p.drawString(66, p._pagesize[1] - 42, SHOP_LIST_HEAD + f'{page}')
        filename = os.path.join(settings.MEDIA_ROOT, 'shop_cart.png')
        p.drawImage(filename, 450, p._pagesize[1] - 138,
                    width=100, height=100, mask='auto')

    @action(detail=False, methods=['get'],
            permission_classes=(permissions.IsAuthenticated,))
    def download_shopping_cart(self, request):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        recipes = Recipe.objects.filter(
            in_shopping_cart__user=self.request.user)
        shopping_list = dict()
        page = 1
        for recipe in recipes:
            ingredients = recipe.ingredients.all()
            for ingredient in ingredients:
                amount = IngredientRecipe.objects.get(recipe=recipe,
                                                      ingredient=ingredient
                                                      ).amount
                if ingredient in shopping_list:
                    shopping_list[ingredient] += amount
                else:
                    shopping_list[ingredient] = amount
        n = 1
        self._page_create(p, page)
        for ingredient, amount in shopping_list.items():
            p.drawString(108, p._pagesize[1] - 138 - n * 20 + (page - 1) * 600,
                         f'{n}. {ingredient.name} - '
                         f'{amount} {ingredient.measurement_unit}')
            n += 1
            if n % SHOP_LIST_ITEMS_PER_PAGE == 1:
                page += 1
                p.restoreState()
                p.showPage()
                self._page_create(p, page)
        p.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True,
                            filename="shop_cart.pdf",
                            status=status.HTTP_200_OK)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk):
        if request.method == 'POST':
            if not Recipe.objects.all().filter(id=pk):
                return Response(RECIPE_NOT_FOUND,
                                status=status.HTTP_400_BAD_REQUEST)
            if Best.objects.filter(user=request.user, recipe__id=pk).exists():
                return Response(ALREADY_IN_BEST,
                                status=status.HTTP_400_BAD_REQUEST)
            recipe = get_object_or_404(Recipe, id=pk)
            Best.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeLimitedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if not Recipe.objects.all().filter(id=pk):
                return Response(RECIPE_NOT_FOUND,
                                status=status.HTTP_404_NOT_FOUND)
            if not Best.objects.filter(user=request.user,
                                       recipe__id=pk).exists():
                return Response(RECIPE_NOT_IN_BEST,
                                status=status.HTTP_400_BAD_REQUEST)
            Best.objects.filter(user=request.user, recipe__id=pk).delete()
            return Response(SUCCESS_REMOVE_FROM_BEST,
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            if not Recipe.objects.all().filter(id=pk):
                return Response(RECIPE_NOT_FOUND,
                                status=status.HTTP_400_BAD_REQUEST)
            if ShopCart.objects.filter(user=request.user,
                                       recipe__id=pk).exists():
                return Response(ALREADY_IN_CART,
                                status=status.HTTP_400_BAD_REQUEST)
            recipe = get_object_or_404(Recipe, id=pk)
            ShopCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeLimitedSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            if not Recipe.objects.all().filter(id=pk):
                return Response(RECIPE_NOT_FOUND,
                                status=status.HTTP_404_NOT_FOUND)
            if not ShopCart.objects.filter(user=request.user,
                                           recipe__id=pk).exists():
                return Response(RECIPE_NOT_IN_CART,
                                status=status.HTTP_400_BAD_REQUEST)
            ShopCart.objects.filter(user=request.user, recipe__id=pk).delete()
            return Response(SUCCESS_REMOVE_FROM_CART,
                            status=status.HTTP_204_NO_CONTENT)
