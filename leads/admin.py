from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "lead_type",
        "source",
        "referred_by",
        "status",
        "next_follow_up_date",
        "next_step",
        "created_at",
    )

    search_fields = (
        "person__first_name",
        "person__last_name",
        "person__email",
        "person__phone",
        "source",
        "notes",
        "next_step",
        "referred_by__first_name",
        "referred_by__last_name",
    )

    list_filter = (
        "lead_type",
        "status",
        "source",
        "referred_by",
        "next_follow_up_date",
        "created_at",
    )

    ordering = ("next_follow_up_date", "-created_at")
    date_hierarchy = "created_at"