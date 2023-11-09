from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from recipes.models import Recipe
from recipes.serializer import RecipeSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageNumberPagination
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

