from rest_framework import viewsets, status, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.forms.models import model_to_dict

from recipes.models import Recipe, Ingredient, Favorite, Tag
from recipes.serializer import (RecipeSerializer, IngredientSerializer,
                                FavoriteSerializer, TagSerializer)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None



class FavoriteDeleteView(generics.DestroyAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated, )

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Favorite.objects.all(),
            user=self.request.user,
            recipe=self.kwargs.get('pk')
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteView(generics.CreateAPIView, generics.DestroyAPIView):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        recipe = get_object_or_404(
            Recipe.objects.all(),
            pk=self.kwargs.get('pk')
        )
        request.data['user'] = self.request.user.id
        request.data['recipe'] = recipe.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return_data = model_to_dict(
            recipe, fields=['id', 'name', 'cooking_time']
        )
        return_data['image'] = request.build_absolute_uri(recipe.image.url)
        headers = self.get_success_headers(serializer.data)
        return Response(return_data, status=status.HTTP_201_CREATED,
                        headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(
            Favorite.objects.all(),
            user=self.request.user,
            recipe=self.kwargs.get('pk')
        )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
