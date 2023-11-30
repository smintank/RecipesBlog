from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, views, status, generics
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
import io
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from recipes.filters import RecipeFilter
from recipes.permissions import IsAuthorOrReadOnly
from recipes.models import (Recipe, Ingredient, Favorite, Tag, Subscription,
                            ShoppingCart, User, RecipeIngredient)
from recipes.serializer import (
    RecipeSerializer, IngredientSerializer, FavoriteSerializer, TagSerializer,
    SubscribeSerializer, ShoppingCartSerializer
)

UNSUB_ERR_MSG = 'Нельзя отписаться, вы не подписаны!'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    http_method_names = ['get', 'post', 'patch', 'delete']

    CHECKED_FILTERS = ('is_favorited', 'is_in_shopping_cart')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def list(self, request, *args, **kwargs):
        # Так я решил проблему фильтров is_favorited=1, is_in_shopping_cart=1
        # Подменив их значения на 'True' или 'False'
        request.query_params._mutable = True
        for param, value in request.query_params.items():
            if param in self.CHECKED_FILTERS and value in ('1', '0'):
                request.query_params[param] = str(bool(int(value)))
        request.query_params._mutable = False

        return super().list(request, *args, **kwargs)


class SubscriptionListView(generics.ListAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscribeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)


class SubscribeView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscribeSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        request.data['user'] = self.request.user.id
        request.data['subscription'] = get_object_or_404(
            User, id=self.kwargs.get('pk')).id
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        subscription = get_object_or_404(User, id=self.kwargs.get('pk')).id
        instance = self.queryset.filter(
            user=self.request.user.id, subscription=subscription
        )
        if not instance:
            return Response(
                {'error': UNSUB_ERR_MSG}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance.first())
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_context(self):
        context = {'request': self.request}
        return context

    def create(self, request, *args, **kwargs):
        request.data['user'] = self.request.user.id
        request.data['recipe'] = self.kwargs.get('pk')
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        instance = self.queryset.filter(
            user=self.request.user.id, recipe=recipe
        )
        if not instance:
            return Response(
                {'error': UNSUB_ERR_MSG}, status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance.first())
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(FavoriteView):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer


class DownloadCartView(views.APIView):
    title_font_size = 16
    text_font_size = 12
    title_x_y = 230, 800
    ingredient_y = 760
    ingredient_x = 70
    amount_x = 450
    y_shift = 25
    file_name = 'groceries.pdf'

    def get(self, request, *args, **kwargs):
        buffer = io.BytesIO()

        response = self._set_settings()
        ingredient_sum = self._get_ingredients_data()

        page = canvas.Canvas(response)
        self._fill_page(ingredient_sum, page)
        page.showPage()
        page.save()

        buffer.seek(0)
        return response

    def _fill_page(self, ingredient_sum, page):
        page.setFont('Roboto-Regular', self.title_font_size)
        page.drawString(*self.title_x_y, text='Список покупок')
        page.setFont('Roboto-Regular', self.text_font_size)
        height = self.ingredient_y
        for i, ingredient in enumerate(ingredient_sum):
            height -= self.y_shift
            name = ingredient['name'].capitalize()
            page.drawString(self.ingredient_x, height, f'{i + 1}. {name}')

            amount = ingredient['amount']
            unit = ingredient['unit']
            page.drawString(self.amount_x, height, f'{amount} {unit}')

    def _get_ingredients_data(self):
        ingredient_set = RecipeIngredient.objects.values(
            'ingredient__name', 'amount', 'ingredient__measurement_unit'
        ).filter(
            recipe__shopping_cart__user=self.request.user.id
        ).order_by('ingredient__name')

        current_ingredient = ''
        ingredient_sum = []
        for item in ingredient_set:
            if item['ingredient__name'] != current_ingredient:
                current_ingredient = item['ingredient__name']
                ingredient_sum.append({
                    'amount': int(item['amount']),
                    'name': item['ingredient__name'],
                    'unit': item['ingredient__measurement_unit']})
            else:
                ingredient_sum[-1]['amount'] += int(item['amount'])
        return ingredient_sum

    def _set_settings(self):
        pdfmetrics.registerFont(TTFont('Roboto-Regular', 'Roboto-Regular.ttf'))
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; ' \
                                          f'filename="{self.file_name}"'

        return response
