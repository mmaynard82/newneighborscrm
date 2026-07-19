from django.contrib import admin
from .models import MaintenanceRequest


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "property",
        "priority",
        "status",
        "assigned_vendor",
        "date_reported",
    )

    search_fields = (
        "title",
        "description",
        "property__address",
        "reported_by__first_name",
        "reported_by__last_name",
        "assigned_vendor__first_name",
        "assigned_vendor__last_name",
    )

    list_filter = (
        "priority",
        "status",
        "date_reported",
    )