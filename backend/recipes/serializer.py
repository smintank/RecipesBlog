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
        if self.context['request'].user.is_anonymous:
            return False
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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True
    )
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image', 'cooking_time', 'tags',
            'ingredients', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
        return Favorite.objects.filter(
            user=self.context['request'].user,
            recipe=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        if self.context['request'].user.is_anonymous:
            return False
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


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True, allow_empty=False)
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    cooking_time = serializers.IntegerField(min_value=1)

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

    def validate_tags(self, data):
        tags = self.initial_data['tags']
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError(
                'Рецепт не может содержать повторяющиеся теги'
            )
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data['ingredients']
        ingredient_set = [ingredient['id'] for ingredient in ingredients]
        if len(set(ingredient_set)) != len(ingredient_set):
            raise serializers.ValidationError(
                'Рецепт не может содержать повторяющиеся ингредиенты'
            )
        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ingredient_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.get_or_create(recipe=instance,
                                                   **ingredient_data)
        instance.text = validated_data.get('text', instance.text)
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.tags.set(validated_data.get('tags', instance.tags))
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()
        return instance

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        instance['ingredients'].clear()
        instance['tags'].clear()
        tags_data = self.validated_data['tags']
        for tag in tags_data:
            tag_set = {
                'id': tag.id,
                'color': tag.color,
                'name': tag.name,
                'slug': tag.slug
            }
            instance['tags'].append(OrderedDict(tag_set))

        for ingredient_data in self.validated_data['ingredients']:
            ingredient = ingredient_data['ingredient']
            ingredient_set = {
                'id': ingredient.id,
                'name': ingredient.name,
                'measurement_unit': ingredient.measurement_unit,
                'amount': ingredient_data['amount']
            }
            instance['ingredients'].append(OrderedDict(ingredient_set))
        return instance


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
