from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action

from recipes.models import Recipe, User
from recipes.serializer import RecipeSerializer, UserSerializer


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
