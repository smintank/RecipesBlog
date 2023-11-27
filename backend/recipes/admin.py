from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import (Recipe, Ingredient, Tag, Subscription, User,
                            Favorite, RecipeIngredient, ShoppingCart)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('name', 'author', 'favorite_count')
    list_filter = ('tags', 'author', 'name')

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return f'{Favorite.objects.filter(recipe=obj.id).count()}'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription')
    list_display_links = ('user', 'subscription')


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


class MyUserAdmin(UserAdmin):
    list_filter = ('email', 'username')


admin.site.register(ShoppingCart)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(User, MyUserAdmin)
admin.site.register(Favorite)
admin.site.register(Ingredient, IngredientsAdmin)
