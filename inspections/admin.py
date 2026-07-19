from django.contrib import admin
from .models import HomeInspection


@admin.register(HomeInspection)
class HomeInspectionAdmin(admin.ModelAdmin):
    list_display = (
        "property",
        "inspection_type",
        "inspection_date",
        "follow_up_needed",
        "next_inspection_date",
    )

    search_fields = (
        "property__address",
        "exterior_notes",
        "interior_notes",
        "safety_concerns",
        "maintenance_needed",
    )

    list_filter = (
        "inspection_type",
        "follow_up_needed",
        "inspection_date",
        "next_inspection_date",
    )