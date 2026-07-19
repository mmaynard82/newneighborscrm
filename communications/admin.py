from django.contrib import admin
from .models import CommunicationLog


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = (
        "person",
        "communication_type",
        "communication_date",
        "outcome",
        "next_follow_up_date",
    )

    search_fields = (
        "person__first_name",
        "person__last_name",
        "subject",
        "summary",
        "next_step",
    )

    list_filter = (
        "communication_type",
        "outcome",
        "communication_date",
        "next_follow_up_date",
    )

    date_hierarchy = "communication_date"