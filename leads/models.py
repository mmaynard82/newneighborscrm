from django.db import models

from people.models import Person
from properties.models import Property


class Lead(models.Model):
    LEAD_TYPES = [
        ("buyer", "Buyer"),
        ("seller", "Seller"),
        ("property_management", "Property Management"),
        ("home_management", "Home Management"),
        ("flat_fee_listing", "Flat-Fee Listing"),
        ("investor", "Investor"),
        ("referral", "Referral"),
        ("probate_estate", "Probate / Estate"),
        ("downsizing", "Downsizing"),
        ("other", "Other"),
    ]

    LEAD_STATUSES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("consult_scheduled", "Consult Scheduled"),
        ("proposal_sent", "Proposal Sent"),
        ("active_client", "Active Client"),
        ("closed", "Closed"),
        ("lost", "Lost"),
        ("nurture", "Nurture"),
    ]

    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="leads",
    )

    lead_type = models.CharField(
        max_length=100,
        choices=LEAD_TYPES,
    )

    source = models.CharField(
        max_length=100,
        blank=True,
    )

    referred_by = models.ForeignKey(
        Person,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referred_leads",
    )

    status = models.CharField(
        max_length=100,
        choices=LEAD_STATUSES,
        default="new",
    )

    related_property = models.ForeignKey(
        Property,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads",
    )

    last_contact_date = models.DateField(
        null=True,
        blank=True,
    )

    next_follow_up_date = models.DateField(
        null=True,
        blank=True,
    )

    next_step = models.CharField(
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["next_follow_up_date", "-created_at"]

    def __str__(self):
        return f"{self.person} - {self.get_lead_type_display()} - {self.get_status_display()}"