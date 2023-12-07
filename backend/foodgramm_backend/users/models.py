from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validator_username
from .constants import (MAX_USERNAME_CHARACTERS, MAX_EMAIL_CHARACTERS,
                        MAX_PASSWORD_CHARACTERS)


class User(AbstractUser):
    """ Класс пользователей. """
    username = models.CharField(
        'Логин',
        max_length=MAX_USERNAME_CHARACTERS,
        unique=True,
        help_text=('Не более 150 символов. '
                   'Только буквы и цифры, символы @+-'),
        validators=(validator_username,),
        error_messages={
            'unique': 'Пользователь с таким именем уже есть',
        }
    )
    email = models.EmailField('E-mail: ', max_length=MAX_EMAIL_CHARACTERS,
                              unique=True)
    first_name = models.CharField('Имя: ',
                                  max_length=MAX_USERNAME_CHARACTERS)
    last_name = models.CharField('Фамилия: ',
                                 max_length=MAX_USERNAME_CHARACTERS)
    password = models.CharField('Пароль', max_length=MAX_PASSWORD_CHARACTERS)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'password', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """ Подписка на пользователя """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription')]

    def __str__(self):
        return f'{self.user} {self.author}'
