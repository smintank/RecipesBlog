from itertools import islice

from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator

from users.models import User, Subscription


class UserSerializer(DjoserUserSerializer):
    is_subscribed = SerializerMethodField()

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


class SubscribeSerializer(ModelSerializer):
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
            raise ValidationError('Вы не можете быть подписаны на себя')
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

        subscription = UserSerializer(instance.subscription,
                                      context=self.context).data
        subscription['recipes'] = recipe_set
        subscription['recipes_count'] = recipes.count()
        return subscription
