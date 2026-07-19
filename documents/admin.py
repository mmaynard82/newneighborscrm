from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "document_type",
        "related_person",
        "related_property",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "notes",
        "related_person__first_name",
        "related_person__last_name",
        "related_property__address",
    )

    list_filter = (
        "document_type",
        "uploaded_at",
    )