from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    REQUIRED_FIELDS = [
        'first_name', 'last_name', 'email'
    ]

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Ingredient(models.Model):
    name = models.CharField(max_length=200)
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Имя',
    )
    color = models.CharField(
        max_length=7,
        verbose_name='Цвет',
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name='Slug',
        unique=True
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
    )
    author = models.ForeignKey(
        User, related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Описание')
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
        verbose_name='Изображение'
    )
    ingredient = models.ManyToManyField(
        Ingredient, verbose_name='Ингридиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги',
        related_name='recipes'
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления'
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


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
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'Пользователь {self.user} подписан на {self.subscription}'
