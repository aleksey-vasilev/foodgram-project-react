from django.urls import include, path
from rest_framework import routers

from .views import TagViewSet


router = routers.SimpleRouter()
router.register('tags', TagViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
