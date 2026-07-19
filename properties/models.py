from django.db import models
from people.models import Person


class Property(models.Model):
    PROPERTY_TYPES = [
        ("single_family", "Single Family"),
        ("condo", "Condo"),
        ("multi_family", "Multi-Family"),
        ("commercial", "Commercial"),
        ("land", "Land"),
        ("rental", "Rental"),
    ]

    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50, default="CT")
    zip_code = models.CharField(max_length=20)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPES, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    square_feet = models.IntegerField(null=True, blank=True)
    owner = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
