"""Opt-in CRM event intake; no outbound network I/O in model signals.

Automated jobs are created only for the single configured CRM workspace and
processed by a separately scheduled management command.
"""
import hashlib
import json
from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from dashboard.access import REAL_ESTATE_ONLY_LEAD_TYPES
from leads.models import Lead
from .models import LeadPilotReview, TransactionCase


ACTIVE_STATES = {"pending", "queued", "running", "retrying", "awaiting_approval", "approved", "completed"}


def enabled_for(workspace_id):
    return (
        getattr(settings, "LEADPILOT_AUTOMATION_ENABLED", False)
        and str(workspace_id) == getattr(settings, "LEADPILOT_CRM_WORKSPACE_ID", "")
        and bool(getattr(settings, "LEADPILOT_BRIDGE_URL", ""))
        and len(getattr(settings, "LEADPILOT_BRIDGE_TOKEN", "")) >= 32
    )


def queue_lead(lead):
    if not lead.workspace_id or not enabled_for(lead.workspace_id):
        return None
    if lead.lead_type not in REAL_ESTATE_ONLY_LEAD_TYPES:
        return None
    if lead.status in ("closed", "lost"):
        return None
    reference = "auto-lead-{}-{}".format(lead.workspace_id, lead.pk)
    review, _ = LeadPilotReview.objects.get_or_create(
        reference=reference,
        defaults={"workspace_id": lead.workspace_id, "lead": lead, "status": "pending"},
    )
    return review


def transaction_signature(case, day):
    """One review per relevant set of terms and day, never a continuous AI loop."""
    dates = [case.inspection_deadline, case.financing_deadline, case.closing_date]
    payload = {
        "stage": case.stage, "inspection": str(dates[0]),
        "financing": str(dates[1]), "closing": str(dates[2]),
        "notes": case.notes or "", "day": str(day),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]


def transaction_needs_attention(case, today):
    if case.stage in ("closed", "cancelled"):
        return False
    dates = (case.inspection_deadline, case.financing_deadline, case.closing_date)
    return any(date and date <= today + timedelta(days=7) for date in dates)


def queue_transaction(case, *, today=None, force=False):
    if not case.workspace_id or not enabled_for(case.workspace_id):
        return None
    if case.stage in ("closed", "cancelled"):
        return None
    today = today or timezone.localdate()
    if not force and not transaction_needs_attention(case, today):
        return None
    # Suppress extra chargeable work on the same deal/day even if contents change.
    recent = LeadPilotReview.objects.filter(
        workspace_id=case.workspace_id, transaction=case,
        created_at__date=today,
    ).exclude(status__in=["unavailable", "failed"]).order_by("-created_at").first()
    if recent:
        return recent
    digest = transaction_signature(case, today)
    reference = "auto-tx-{}-{}-{}".format(case.workspace_id, case.pk, digest)
    review, _ = LeadPilotReview.objects.get_or_create(
        reference=reference,
        defaults={"workspace_id": case.workspace_id, "transaction": case, "status": "pending"},
    )
    return review


@receiver(post_save, sender=Lead, dispatch_uid="crm_auto_queue_new_lead")
def new_sales_lead(sender, instance, created, **kwargs):
    if created:
        queue_lead(instance)


@receiver(post_save, sender=TransactionCase, dispatch_uid="crm_auto_queue_new_transaction")
def new_sales_transaction(sender, instance, created, **kwargs):
    if created:
        queue_transaction(instance, force=True)
