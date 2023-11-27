from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import (Recipe, Ingredient, Tag, Subscription, User,
                            Favorite, RecipeIngredient, ShoppingCart)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class IngredientAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('id', 'name', 'author', 'text', 'cooking_time')
    list_filter = ('author',)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription')


admin.site.register(ShoppingCart)
admin.site.register(Recipe, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Favorite)
admin.site.register(Ingredient)
