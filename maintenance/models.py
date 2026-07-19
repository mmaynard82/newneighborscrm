from django.db import models
from people.models import Person
from properties.models import Property


class MaintenanceRequest(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("assigned", "Assigned"),
        ("in_progress", "In Progress"),
        ("waiting_on_vendor", "Waiting on Vendor"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("emergency", "Emergency"),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    reported_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_maintenance_requests",
    )
    assigned_vendor = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_maintenance_requests",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default="normal")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="new")
    date_reported = models.DateField(auto_now_add=True)
    date_completed = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.property} - {self.title}"