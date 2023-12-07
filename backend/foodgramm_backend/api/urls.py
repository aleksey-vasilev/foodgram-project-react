from django.urls import include, path
from rest_framework import routers

from .views import (TagViewSet, UserSubscriptionViewSet,
                    UserSubscribeViewSet, IngredientViewSet,
                    RecipeViewSet)


router = routers.SimpleRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('users/subscriptions', UserSubscriptionViewSet, basename='subscriptions')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('users/<int:author_id>/subscribe/', UserSubscribeViewSet.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
