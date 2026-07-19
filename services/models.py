from django.db import models
from people.models import Person
from properties.models import Property


class Service(models.Model):
    SERVICE_TYPES = [
        ("buyer_representation", "Buyer Representation"),
        ("seller_representation", "Seller Representation"),
        ("property_management", "Property Management"),
        ("home_management", "Home Management"),
        ("flat_fee_listing", "Flat-Fee Listing"),
        ("vacant_property_watch", "Vacant Property Watch"),
        ("repair_coordination", "Repair Coordination"),
    ]

    SERVICE_STATUSES = [
        ("inquiry", "Inquiry"),
        ("proposal_sent", "Proposal Sent"),
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    client = models.ForeignKey(Person, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True)
    service_type = models.CharField(max_length=100, choices=SERVICE_TYPES)
    status = models.CharField(max_length=100, choices=SERVICE_STATUSES, default="inquiry")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.client} - {self.service_type}"
