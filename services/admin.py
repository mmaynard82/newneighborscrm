from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("client", "property", "service_type", "status", "monthly_fee", "start_date")
    search_fields = ("client__first_name", "client__last_name", "property__address")
    list_filter = ("service_type", "status")