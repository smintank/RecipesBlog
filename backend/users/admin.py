from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscription, User


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription')


class MyUserAdmin(UserAdmin):
    list_filter = ('email', 'username', 'is_superuser', 'is_active')


admin.site.register(User, MyUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
