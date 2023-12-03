from base64 import b64decode
from collections import OrderedDict

from django.core.files.base import ContentFile
from django.db.models import F
from rest_framework.serializers import (ImageField, IntegerField,
                                        ModelSerializer,
                                        PrimaryKeyRelatedField,
                                        SerializerMethodField,
                                        ValidationError)
from rest_framework.validators import UniqueTogetherValidator

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
                {'tags': ['Значения не должны повторяться']}
            )
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data['ingredients']
        ingredient_set = [ingredient['id'] for ingredient in ingredients]
        if len(set(ingredient_set)) != len(ingredient_set):
            raise ValidationError(
                {'ingredients': ['Значения не должны повторяться']}
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


class FavoriteSerializer(ModelSerializer):
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
