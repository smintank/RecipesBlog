from rest_framework import viewsets, views, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from recipes.models import Recipe, User, Ingredient, Favorite
from recipes.serializer import (RecipeSerializer, UserSerializer,
                                IngredientSerializer, FavoriteSerializer)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer


class FavoriteAPIView(views.APIView):
    def post(self, request, pk):
        user = self.request.user
        recipe = get_object_or_404(Recipe.objects.all(), pk=pk)
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {'errors': 'Вы уже подписаны на этот рецепт'},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.data['user'] = user.id
        request.data['recipe'] = recipe.id

        serializer = FavoriteSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        recipe = get_object_or_404(Recipe.objects.all(), pk=pk)
        user = self.request.user.id
        instance = Favorite.objects.filter(user=user, recipe=recipe.id)
        if not instance.exists():
            return Response(
                {'errors': 'У вас в избранном нет этого рецепта'},
                status=status.HTTP_400_BAD_REQUEST)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer

    @action(detail=False, methods=['GET'])
    def me(self, request):
        self.kwargs['pk'] = request.user.id
        return self.retrieve(request)
