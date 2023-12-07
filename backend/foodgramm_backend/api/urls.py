from django.urls import include, path
from rest_framework import routers

from .views import TagViewSet, UserSubscriptionViewSet, UserSubscribeViewSet


router = routers.SimpleRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('users/subscriptions', UserSubscriptionViewSet, basename='subscriptions')
router.register(r'users/(?P<author_id>\d+)/subscribe', UserSubscribeViewSet, basename='subscribe')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
