from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from rest_framework import routers

from foodgram import settings

from recipes.views import (RecipeViewSet, IngredientViewSet, FavoriteView,
                           TagViewSet, SubscribeView, SubscriptionListView,
                           ShoppingCartView, DownloadCartView)

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet, basename='recipe')
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/<int:pk>/subscribe/', SubscribeView.as_view()),
    path('api/users/subscriptions/', SubscriptionListView.as_view()),
    path('api/recipes/<int:pk>/favorite/', FavoriteView.as_view()),
    path('api/recipes/<int:pk>/shopping_cart/', ShoppingCartView.as_view()),
    path('api/recipes/download_shopping_cart/', DownloadCartView.as_view()),
    path('api/', include(router.urls)),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
