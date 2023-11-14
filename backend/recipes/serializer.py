from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
import base64
from django.core.files.base import ContentFile

from recipes.models import Ingredient, Tag, Recipe, User, Subscription


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
        read_only_fields = ('id',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'color', 'slug'
        )
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(required=False, many=True)
    tags = TagSerializer(required=False, many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'image', 'cooking_time',
            'tags', 'ingredients', 'author'
        )
        read_only_fields = ('id', 'author')


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            RegexValidator(regex=r'^[\w.@+-]+\z'),
            UniqueValidator(queryset=User.objects.all())
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(queryset=User.objects.all())
        ]
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        return Subscription.objects.filter(
            user=self.context['request'].user,
            subscription=obj.id
        ).exists()

