from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import (permissions, status, viewsets)
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (UserSerializer, FollowSerializer, TagSerializer)
from .pagination import UsersPagination
from users.models import Follow
from recipes.models import Tag

User = get_user_model()

class TagViewSet(viewsets.ModelViewSet):
    """ Получение тегов """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    http_method_names = ('get',)

class UserSubscriptionViewSet(viewsets.ModelViewSet):
    """ Получение списка подписанных пользователей """
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ('get',)

    def get(self, request):
        queryset = Follow.objects.filter(user=self.request.user)
        serializer = FollowSerializer(queryset,
                                      many=True,
                                      context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserSubscribeViewSet(viewsets.ModelViewSet):
    """ Подписка и отписка от пользователя """
    serializer_class = FollowSerializer

    def post(self, request):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        user = self.request.user
        serializer = FollowSerializer(data=request.data,
                                      context={'request': request, 'author': author})
        if serializer.is_valid(raise_exception=True):
            serializer.save(author=author, user=user)
            return Response({'Подписка успешно создана': serializer.data},
                            status=status.HTTP_201_CREATED)
        return Response({'errors': 'Объект не найден'},
                        status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        author = get_object_or_404(User, id=self.kwargs.get('author_id'))
        user = self.request.user
        if Follow.objects.filter(author=author, user=user).exists():
            Follow.objects.get(author=author).delete()
            return Response('Успешная отписка',
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'errors': 'Объект не найден'},
                        status=status.HTTP_404_NOT_FOUND)