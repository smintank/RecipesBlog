from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from django.core.files.base import ContentFile

import djoser.serializers
import base64

from foodgram.settings import AUTH_USER_MODEL as USER
from recipes.models import Ingredient, Tag, Recipe, Subscription, Favorite


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id', 'name', 'measurement_unit'
        )
        read_only_fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color', 'slug'
        )
        read_only_fields = ('id',)


class UserSerializer(djoser.serializers.UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = USER
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=self.context['request'].user.id,
            subscription=obj.id
        ).exists()


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(required=False, many=True)
    tags = TagSerializer(required=False, many=True)
    author = UserSerializer(required=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image', 'cooking_time', 'tags',
            'ingredients', 'author', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = (
            'id', 'author' 'is_favorited', 'is_in_shopping_cart', 'tags',
            'ingredients')

    def get_is_favorited(self, obj):
        return Favorite.objects.filter(
            user=self.context['request'].user,
            recipe=obj.id
        ).exists()


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe')
            )
        ]

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed'
        )






