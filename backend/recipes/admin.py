from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from recipes.models import (Recipe, Ingredient, Tag, Subscription, User,
                            Favorite, RecipeIngredient, ShoppingCart)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    verbose_name = 'ингредиент'
    verbose_name_plural = 'Ингредиенты'
    fields = ('ingredient', 'amount')


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'favorite_count')
    list_filter = ('tags', )
    search_fields = ('name',)
    filter_horizontal = ('tags',)
    date_hierarchy = 'pub_date'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            _favorite_count=Count("favorites", distinct=True),
        )
        return queryset

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        count = obj._favorite_count
        if count == 0:
            return 'нет'
        return f'{count}'

    favorite_count.admin_order_field = '_favorite_count'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription')
    list_display_links = ('user', 'subscription')


class IngredientsAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class MyUserAdmin(UserAdmin):
    list_filter = ('email', 'username', 'is_superuser', 'is_active')


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientsAdmin)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
admin.site.register(Tag)

admin.site.register(User, MyUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
