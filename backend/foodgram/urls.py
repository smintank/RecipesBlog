from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework import routers

from foodgram import settings

from recipes.views import (RecipeViewSet, UserViewSet, IngredientViewSet,
                           FavoriteAPIView)

router = routers.DefaultRouter()
router.register('users', UserViewSet)
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/recipes/<int:pk>/favorite/', FavoriteAPIView.as_view()),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
