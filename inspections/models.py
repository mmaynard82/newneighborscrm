from django.db import models
from properties.models import Property


class HomeInspection(models.Model):
    INSPECTION_TYPES = [
        ("routine", "Routine"),
        ("seasonal", "Seasonal"),
        ("move_in", "Move-In"),
        ("move_out", "Move-Out"),
        ("emergency", "Emergency"),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    inspection_type = models.CharField(
        max_length=50,
        choices=INSPECTION_TYPES,
        default="routine",
    )
    inspection_date = models.DateField()
    exterior_notes = models.TextField(blank=True)
    interior_notes = models.TextField(blank=True)
    safety_concerns = models.TextField(blank=True)
    maintenance_needed = models.TextField(blank=True)
    follow_up_needed = models.BooleanField(default=False)
    next_inspection_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property} - {self.inspection_date}"