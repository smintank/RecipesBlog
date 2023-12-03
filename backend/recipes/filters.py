from django_filters import (BooleanFilter, CharFilter, FilterSet,
                            ModelMultipleChoiceFilter)

from recipes.models import Recipe, Tag


class RecipeFilter(FilterSet):
    author = CharFilter()
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        label='Tags',
        to_field_name='slug'

    )
    is_favorited = CharFilter(method='get_is_favorited')
    is_in_shopping_cart = CharFilter(method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_in_shopping_cart', 'is_favorited')

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value.lower() in ('1', 'true') and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value.lower() in ('1', 'true') and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IngredientFilter(FilterSet):
    name = CharFilter(method='get_name')

    def get_name(self, queryset, name, value):
        return queryset.filter(name__icontains=value)
