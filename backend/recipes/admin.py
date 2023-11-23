from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import (Recipe, Ingredient, Tag, Subscription, User,
                            Favorite, RecipeIngredient)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class IngredientAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]


admin.site.register(Recipe, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(Subscription)
admin.site.register(User, UserAdmin)
admin.site.register(Favorite)
admin.site.register(Ingredient)
