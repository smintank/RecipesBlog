from collections import OrderedDict
from django.core.files.base import ContentFile
from django.forms.models import model_to_dict
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

import base64
import djoser.serializers

from recipes.models import (Ingredient, RecipeIngredient, Tag, Recipe,
                            Subscription, Favorite, User, ShoppingCart)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=self.context['request'].user.id,
            subscription=obj.id
        ).exists()


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'ingredient', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(default=False,
                                                   read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image', 'cooking_time', 'tags',
            'ingredients', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        return Favorite.objects.filter(
            user=self.context['request'].user,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(
            user=self.context['request'].user,
            recipe=obj.id
        ).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
        write_only=True
    )
    amount = serializers.IntegerField(min_value=1, write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True, read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(default=False,
                                                   read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image', 'cooking_time', 'tags',
            'ingredients', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

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
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен в избранное',
            ),
        ]

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        recipe = Recipe.objects.get(id=instance['recipe'])
        new_data = {'id': recipe.id,
                    'name': recipe.name,
                    'cooking_time': recipe.cooking_time,
                    'image': self.context['request'].build_absolute_uri(
                        recipe.image.url)
                    }
        return new_data


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'subscription')

    def validate(self, data):
        if data['user'] == data['subscription']:
            raise serializers.ValidationError(
                'Вы не можете быть подписаны на себя'
            )
        if Subscription.objects.filter(
                user=data['user'],
                subscription=data['subscription']
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )
        return data

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        user = User.objects.get(id=instance['subscription'])
        recipes = Recipe.objects.filter(author=user.id)
        recipe_set = []
        for recipe in recipes:
            result = model_to_dict(recipe,
                                   fields=['id', 'name', 'cooking_time'])
            result['image'] = self.context['request'].build_absolute_uri(
                recipe.image.url)
            recipe_set.append(result)

        new_data = {'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_subscribed': True,
                    'recipes': recipe_set,
                    'recipes_count': recipes.count()}
        return new_data


class SubscriptionListSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'subscription')


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен в корзину',
            ),
        ]

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        recipe = Recipe.objects.get(id=instance['recipe'])
        new_data = {'id': recipe.id,
                    'name': recipe.name,
                    'cooking_time': recipe.cooking_time,
                    'image': self.context['request'].build_absolute_uri(
                        recipe.image.url)
                    }
        return new_data


class DownloadCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = ('id', 'ingredient_amount', 'user')
