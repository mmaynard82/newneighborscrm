"""Best-effort, post-commit email notifications for landing-page leads."""
import logging

from django.conf import settings
from django.core.mail import send_mail

from accounts.models import Membership
from leads.models import Lead

logger = logging.getLogger(__name__)


def notify_assigned_agent(lead_id):
    """Never prevent inquiry intake because email is unavailable."""
    if not settings.CRM_AGENT_EMAIL_NOTIFICATIONS:
        return
    if not settings.EMAIL_HOST or not settings.DEFAULT_FROM_EMAIL:
        logger.warning("Lead %s: CRM email notification enabled without complete SMTP setup", lead_id)
        return

    lead = Lead.objects.select_related("workspace", "assigned_agent").filter(pk=lead_id).first()
    if not lead or not lead.workspace_id or not lead.assigned_agent_id:
        return
    agent = lead.assigned_agent
    if not agent.is_active or not agent.email:
        return
    if not Membership.objects.filter(workspace_id=lead.workspace_id, user_id=agent.pk, is_active=True).exists():
        return

    lead_url = settings.CRM_PUBLIC_BASE_URL.rstrip("/") + "/lead/{}/".format(lead.pk)
    subject = "New landing-page lead assigned to you | New Neighbors CRM"
    body = (
        "A new website inquiry has been saved in New Neighbors CRM and assigned to you.\n\n"
        "Workspace: {}\n"
        "Lead ID: {}\n"
        "Open lead: {}\n\n"
        "Please sign in to the CRM to view the contact details and complete your follow-up task.\n"
        "This is an operational notification, not a marketing message."
    ).format(lead.workspace.name, lead.pk, lead_url)
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [agent.email], fail_silently=False)
    except Exception:
        logger.exception("Failed to send assigned-agent notification for lead %s", lead_id)
