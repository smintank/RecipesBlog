from itertools import islice
from collections import OrderedDict
from django.core.files.base import ContentFile
from django.db.models import F
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
        user = self.context['request'].user
        return (user.is_authenticated
                and obj.subscriptions.filter(user=user).exists())


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
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
    ingredients = RecipeIngredientSerializer(many=True, allow_empty=False)
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
        user = self.context['request'].user
        return (user.is_authenticated
                and obj.favorites.filter(user=user).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and obj.shopping_cart.filter(user=user).exists())

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
        if not validated_data.get('tags'):
            raise serializers.ValidationError('tags - обязательное поле')
        try:
            ingredients_data = validated_data.pop('ingredients')
        except Exception:
            raise serializers.ValidationError(
                'ingredients - обязательное поле'
            )

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
        tags = instance.tags.values()
        ingredients = instance.ingredients.values(
            'id', 'name', 'measurement_unit',
            amount=F('recipe_ingredients__amount')
        )
        instance = super().to_representation(instance)
        instance['tags'] = [OrderedDict(tag) for tag in tags]
        instance['ingredients'] = [
            OrderedDict(ingredient) for ingredient in ingredients
        ]
        return instance


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('user', 'subscription')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'subscription'),
                message='Вы уже подписаны на этого пользователя',
            ),
        ]

    def validate(self, data):
        if data['user'] == data['subscription']:
            raise serializers.ValidationError(
                'Вы не можете быть подписаны на себя'
            )
        return data

    def to_representation(self, instance):
        request = self.context['request']
        if recipe_limit := request.query_params.get('recipes_limit'):
            recipe_limit = int(recipe_limit)

        recipes = instance.subscription.recipes
        recipe_set = []
        for recipe in islice(recipes.all(), recipe_limit):
            recipe_set.append({
                'id': recipe.id,
                'name': recipe.name,
                'cooking_time': recipe.cooking_time,
                'image': request.build_absolute_uri(recipe.image.url)
            })

        return {
            'id': instance.subscription.id,
            'username': instance.subscription.username,
            'first_name': instance.subscription.first_name,
            'last_name': instance.subscription.last_name,
            'email': instance.subscription.email,
            'is_subscribed': True,
            'recipes': recipe_set,
            'recipes_count': recipes.count()
        }


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен',
            ),
        ]

    def to_representation(self, instance):
        build_full_url = self.context['request'].build_absolute_uri
        return {'id': instance.recipe.id,
                'name': instance.recipe.name,
                'cooking_time': instance.recipe.cooking_time,
                'image': build_full_url(instance.recipe.image.url)}


class ShoppingCartSerializer(FavoriteSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже добавлен',
            ),
        ]
