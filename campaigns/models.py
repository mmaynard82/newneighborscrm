from django.db import models

from leads.models import Lead
from tags.models import Tag


class Campaign(models.Model):
    CAMPAIGN_TYPES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("phone", "Phone Call"),
        ("mail", "Direct Mail"),
        ("social", "Social Media"),
        ("other", "Other"),
    ]

    CAMPAIGN_STATUSES = [
        ("draft", "Draft"),
        ("audience_built", "Audience Built"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("paused", "Paused"),
        ("cancelled", "Cancelled"),
    ]

    name = models.CharField(max_length=255)
    campaign_type = models.CharField(
        max_length=50,
        choices=CAMPAIGN_TYPES,
        default="email",
    )
    status = models.CharField(
        max_length=50,
        choices=CAMPAIGN_STATUSES,
        default="draft",
    )

    audience_lead_type = models.CharField(max_length=100, blank=True)
    audience_lead_status = models.CharField(max_length=100, blank=True)
    audience_tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    leads = models.ManyToManyField(
        Lead,
        through="CampaignMember",
        blank=True,
        related_name="campaigns",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class CampaignMember(models.Model):
    MEMBER_STATUSES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("responded", "Responded"),
        ("not_interested", "Not Interested"),
        ("converted", "Converted"),
        ("removed", "Removed"),
    ]

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name="members",
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name="campaign_members",
    )

    status = models.CharField(
        max_length=50,
        choices=MEMBER_STATUSES,
        default="queued",
    )

    added_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("campaign", "lead")
        ordering = ["lead__person__last_name", "lead__person__first_name"]

    def __str__(self):
        return f"{self.campaign} - {self.lead}"