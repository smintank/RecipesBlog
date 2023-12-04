from django.contrib.auth.models import AbstractUser
from django.db import models

from recipes.constants import MAX_USER_FIELDS_LENGTH


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=MAX_USER_FIELDS_LENGTH,
                                  blank=False)
    last_name = models.CharField(max_length=MAX_USER_FIELDS_LENGTH,
                                 blank=False)

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик',
    )
    subscription = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписан на'
    )

    class Meta:
        ordering = ('user', 'subscription')
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        models.UniqueConstraint(
            fields=['user', 'subscription'],
            name='user_user_subscription'
        )
