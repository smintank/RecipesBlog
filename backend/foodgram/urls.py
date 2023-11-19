from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework import routers

from foodgram import settings

from recipes.views import (RecipeViewSet, IngredientViewSet, FavoriteView,
                           TagViewSet)

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/recipes/<int:pk>/favorite/', FavoriteView.as_view()),
    path('api/', include(router.urls)),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
