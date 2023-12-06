from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import Subscription, User


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    verbose_name = 'подписка'
    verbose_name_plural = 'Подписки'
    fields = ('subscription',)
    fk_name = 'user'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription')


class MyUserAdmin(UserAdmin):
    list_filter = ('email', 'username', 'is_superuser', 'is_active')
    inlines = [SubscriptionInline]
    readonly_fields = ('last_login', 'date_joined')


admin.site.register(User, MyUserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
admin.site.unregister(Group)
