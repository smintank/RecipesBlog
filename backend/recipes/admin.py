from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import (Recipe, Ingredient, Tag, Subscription, User,
                            Favorite, IngredientAmount)


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    extra = 1


class IngredientAdmin(admin.ModelAdmin):
    inlines = [IngredientAmountInline]


admin.site.register(Recipe)
admin.site.register(Tag)
admin.site.register(Subscription)
admin.site.register(User, UserAdmin)
admin.site.register(Favorite)
admin.site.register(Ingredient)
