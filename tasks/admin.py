from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "related_person", "related_property", "due_date", "priority", "status")
    search_fields = ("title", "description", "related_person__first_name", "related_person__last_name")
    list_filter = ("status", "priority", "due_date")