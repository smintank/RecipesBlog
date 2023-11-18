from django.contrib import admin

from recipes.models import Recipe, Ingredient, Tag, Subscription, User, Favorite

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tag)
admin.site.register(Subscription)
admin.site.register(User, UserAdmin)
admin.site.register(Favorite)
