from django.db import models
from people.models import Person
from properties.models import Property


class Document(models.Model):
    DOCUMENT_TYPES = [
        ("contract", "Contract"),
        ("listing_agreement", "Listing Agreement"),
        ("disclosure", "Disclosure"),
        ("inspection_report", "Inspection Report"),
        ("photo", "Photo"),
        ("invoice", "Invoice"),
        ("repair_photo", "Repair Photo"),
        ("home_management_report", "Home Management Report"),
        ("property_management_report", "Property Management Report"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=100,
        choices=DOCUMENT_TYPES,
        default="other",
    )
    file = models.FileField(upload_to="documents/")
    related_person = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title