from django.db import models
from people.models import Person
from properties.models import Property


class Task(models.Model):
    TASK_STATUSES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITIES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    related_person = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    related_property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=TASK_STATUSES, default="open")
    priority = models.CharField(max_length=50, choices=PRIORITIES, default="normal")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title