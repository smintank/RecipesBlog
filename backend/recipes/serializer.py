from base64 import b64decode
from collections import OrderedDict

from django.core.files.base import ContentFile
from django.db.models import F
from rest_framework.serializers import (CharField, ImageField, IntegerField,
                                        ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField, ValidationError)
from rest_framework.validators import UniqueTogetherValidator

from recipes.constants import Messages
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.serializer import UserSerializer


class Base64ImageField(ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, value):
        return self.context['request'].build_absolute_uri(value.url)


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color', 'slug'
        )
        read_only_fields = ('id',)


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
        write_only=True
    )
    amount = IntegerField(min_value=1, write_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, allow_empty=False)
    author = UserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)
    cooking_time = IntegerField(min_value=1, max_value=600)

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
            raise ValidationError(
                {'tags': [Messages.NOT_UNIQUE_ERROR]}
            )
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data['ingredients']
        ingredient_set = [ingredient['id'] for ingredient in ingredients]
        if len(set(ingredient_set)) != len(ingredient_set):
            raise ValidationError(
                {'ingredients': [Messages.NOT_UNIQUE_ERROR]}
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
            raise ValidationError({'tags': [Messages.REQUIRED_FIELD_ERROR]})
        if not validated_data.get('ingredients'):
            raise ValidationError(
                {'ingredients': [Messages.REQUIRED_FIELD_ERROR]}
            )
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ingredient in validated_data.pop('ingredients'):
            RecipeIngredient.objects.create(recipe=instance, **ingredient)

        return super().update(instance, validated_data)

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


class FavoriteSerializer(ModelSerializer):
    id = IntegerField(source='recipe.id', read_only=True)
    name = CharField(source='recipe.name', read_only=True)
    cooking_time = IntegerField(source='recipe.cooking_time', read_only=True)
    image = Base64ImageField(source='recipe.image', read_only=True)

    class Meta:
        model = Favorite
        fields = (
            'recipe', 'user', 'id', 'name', 'cooking_time', 'image')
        extra_kwargs = {'user': {'write_only': True},
                        'recipe': {'write_only': True}}
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message=Messages.ALREADY_EXISTING_ERROR,
            ),
        ]


class ShoppingCartSerializer(FavoriteSerializer):
    class Meta(FavoriteSerializer.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'recipe'),
                message=Messages.ALREADY_EXISTING_ERROR,
            ),
        ]
