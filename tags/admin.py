from django.contrib import admin
from .models import Tag, PersonTag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "category")
    search_fields = ("name", "description")
    list_filter = ("category",)


@admin.register(PersonTag)
class PersonTagAdmin(admin.ModelAdmin):
    list_display = ("person", "tag", "added_at")
    search_fields = (
        "person__first_name",
        "person__last_name",
        "tag__name",
    )
    list_filter = ("tag", "added_at")