import io

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from recipes.constants import Messages, PdfSettings
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from recipes.permissions import IsAuthorOrReadOnly
from recipes.serializer import (FavoriteSerializer, IngredientSerializer,
                                RecipeSerializer, ShoppingCartSerializer,
                                TagSerializer)


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

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,),
            serializer_class=FavoriteSerializer,
            queryset=Favorite.objects.all())
    def favorite(self, request, pk=None):
        request.data['user'] = request.user.id
        request.data['recipe'] = pk

        if request.method == 'POST':
            serializer = self.get_serializer(data=request.data,
                                             context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED,
                            headers=headers)

        elif request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            instance = self.queryset.filter(user=request.user, recipe=recipe)
            if not instance:
                return Response({'error': Messages.NOT_EXISTING_ERROR},
                                status=status.HTTP_400_BAD_REQUEST)
            self.perform_destroy(instance.first())
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['POST', 'DELETE'],
            permission_classes=(IsAuthenticated,),
            serializer_class=ShoppingCartSerializer,
            queryset=ShoppingCart.objects.all())
    def shopping_cart(self, request, pk=None):
        return self.favorite(request, pk)


class DownloadCartView(views.APIView):

    def get(self, request, *args, **kwargs):
        buffer = io.BytesIO()
        response = self._set_settings(
            filename=PdfSettings.FILE_NAME,
            font=PdfSettings.FONT,
            font_path=PdfSettings.FONT_PATH
        )
        grocery_list = self._get_grocery_list(user_id=self.request.user.id)

        page = canvas.Canvas(response)
        self._fill_page(
            grocery_list=grocery_list, page=page, settings=PdfSettings
        )
        page.showPage()
        page.save()

        buffer.seek(0)
        return response

    @staticmethod
    def _fill_page(grocery_list, page, settings):
        page.setFont(settings.FONT, settings.TITLE_FONT_SIZE)
        page.drawString(*settings.TITLE_X_Y, text=settings.TITLE_TEXT)
        page.setFont(settings.FONT, settings.TEXT_FONT_SIZE)
        row_y = settings.ROW_START_Y

        for i, item in enumerate(grocery_list, start=1):
            row_y -= settings.ROW_SHIFT_Y
            name = item['name'].capitalize()
            amount = item['amount_sum']
            unit = item['measurement_unit']

            page.drawString(settings.INGREDIENT_X, row_y, f'{i}. {name}')
            page.drawString(settings.AMOUNT_X, row_y, f'{amount} {unit}')

    @staticmethod
    def _get_grocery_list(user_id):
        ingredient_set = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=user_id
        ).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')
        ).annotate(
            amount_sum=Sum('amount')
        ).order_by('name')

        return ingredient_set

    @staticmethod
    def _set_settings(filename, font=None, font_path=None):
        if font and font_path:
            pdfmetrics.registerFont(TTFont(font, font_path))
        response = HttpResponse(content_type='application/pdf')
        content_disposition = f'attachment; filename="{filename}"'
        response['Content-Disposition'] = content_disposition
        return response
