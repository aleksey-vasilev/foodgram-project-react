from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, Q

from .validators import validator_username
from .constants import MAX_USERNAME_CHARACTERS, MAX_EMAIL_CHARACTERS


class User(AbstractUser):
    """ Класс пользователей. """

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'password', 'first_name', 'last_name')

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
    email = models.EmailField('E-mail', max_length=MAX_EMAIL_CHARACTERS,
                              unique=True)
    first_name = models.CharField('Имя',
                                  max_length=MAX_USERNAME_CHARACTERS)
    last_name = models.CharField('Фамилия',
                                 max_length=MAX_USERNAME_CHARACTERS)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Follow(models.Model):
    """ Класс для подписки на автора. """

    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Позписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following',
                               verbose_name='Автор')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                check=(
                    ~Q(user=F('author'))),
                name='prevent_self_follow',
            )
        ]

    def __str__(self):
        return self.user.username
