from django.contrib import admin
from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("address", "city", "state", "zip_code", "property_type", "owner")
    search_fields = ("address", "city", "zip_code")
    list_filter = ("property_type", "city", "state")