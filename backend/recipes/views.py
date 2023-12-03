import io

from django.db.models import IntegerField, F
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, status, views, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from recipes.permissions import IsAuthorOrReadOnly
from recipes.serializer import (FavoriteSerializer, IngredientSerializer,
                                RecipeSerializer, ShoppingCartSerializer,
                                TagSerializer)
from users.views import UNSUB_ERR_MSG


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


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

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


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
        instance = self.queryset.filter(user=request.user, recipe=recipe)
        if not instance:
            return Response({'error': UNSUB_ERR_MSG},
                            status=status.HTTP_400_BAD_REQUEST)
        self.perform_destroy(instance.first())
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartView(FavoriteView):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer


class DownloadCartView(views.APIView):
    SETTINGS = {
        'file_name': 'groceries.pdf',
        'title_text': 'Список покупок',
        'title_x_y': (230, 800),
        'font': 'Roboto-Regular',
        'font_path': 'Roboto-Regular.ttf',
        'title_font_size': 16,
        'text_font_size': 12,
        'ingredient_x': 70,
        'amount_x': 450,
        'row_start_y': 760,
        'row_shift_y': 25,
    }

    def get(self, request, *args, **kwargs):
        buffer = io.BytesIO()
        response = self._set_settings(
            filename=self.SETTINGS['file_name'],
            font=self.SETTINGS['font'],
            font_path=self.SETTINGS['font_path']
        )
        grocery_list = self._get_grocery_list(user_id=self.request.user.id)

        page = canvas.Canvas(response)
        self._fill_page(
            grocery_list=grocery_list, page=page, settings=self.SETTINGS
        )
        page.showPage()
        page.save()

        buffer.seek(0)
        return response

    @staticmethod
    def _fill_page(grocery_list, page, settings):
        page.setFont(settings['font'], settings['title_font_size'])
        page.drawString(*settings['title_x_y'], text=settings['title_text'])
        page.setFont(settings['font'], settings['text_font_size'])
        row_y = settings['row_start_y']

        for i, item in enumerate(grocery_list, start=1):
            row_y -= settings['row_shift_y']
            name = item['name'].capitalize()
            amount = item['amount']
            unit = item['measurement_unit']

            page.drawString(settings['ingredient_x'], row_y, f'{i}. {name}')
            page.drawString(settings['amount_x'], row_y, f'{amount} {unit}')

    @staticmethod
    def _get_grocery_list(user_id):
        ingredient_set = RecipeIngredient.objects.values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(
            amount=Cast('amount', IntegerField())
        ).filter(
            recipe__shopping_cart__user=user_id
        ).order_by('name')

        ingredient_sum = []
        for item in ingredient_set:
            if ingredient_sum and item['name'] == ingredient_sum[-1]['name']:
                ingredient_sum[-1]['amount'] += item['amount']
            else:
                ingredient_sum.append(item)
        return ingredient_sum

    @staticmethod
    def _set_settings(filename, font=None, font_path=None):
        if font and font_path:
            pdfmetrics.registerFont(TTFont(font, font_path))
        response = HttpResponse(content_type='application/pdf')
        content_disposition = f'attachment; filename="{filename}"'
        response['Content-Disposition'] = content_disposition
        return response
