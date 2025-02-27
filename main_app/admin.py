# Register your models here.

from django.contrib import admin
from .models import GitInstance, ElnConnection, ShuttleInstance


@admin.register(GitInstance)
class GitInstanceAdmin(admin.ModelAdmin):
    list_display = ["name", "url", "branch", "is_active", "last_reload"]
    def save_model(self, request, obj, form, change):
        if obj.active:
            ElnConnection.objects.all().update(active=False)
        super().save_model(request, obj, form, change)


@admin.register(ElnConnection)
class ElnConnectionAdmin(admin.ModelAdmin):
    list_display = ["identifier", "active"]
    def save_model(self, request, obj, form, change):
        if obj.active:
            ElnConnection.objects.all().update(active=False)
        super().save_model(request, obj, form, change)


@admin.register(ShuttleInstance)
class ShuttleInstanceAdmin(admin.ModelAdmin):
    list_display = ["name", "dst"]