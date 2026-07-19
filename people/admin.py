from django.contrib import admin
from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "person_type",
        "preferred_contact_method",
        "email_opt_in",
        "sms_opt_in",
        "do_not_contact",
        "created_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "notes",
    )

    list_filter = (
        "person_type",
        "preferred_contact_method",
        "email_opt_in",
        "sms_opt_in",
        "do_not_contact",
        "created_at",
    )