"""Landing-page lead processing; exposed only to authenticated testing workflows for now."""
from django.db import transaction
from people.models import Person
from leads.models import Lead
from tasks.models import Task
from accounts.models import Membership

TEMPLATE_TO_LEAD_TYPE = {
    "valuation": "seller",
    "probate": "probate_estate",
    "property_management": "property_management",
    "downsizing": "downsizing",
    "open_house": "buyer",
    "custom": "other",
}


@transaction.atomic
def create_landing_inquiry(page, cleaned):
    """Create a lead and follow-up task inside the page's workspace."""
    email = cleaned["email"].strip().lower()
    person = Person.objects.filter(workspace=page.workspace, email__iexact=email).first()
    if person is None:
        person = Person.objects.create(
            workspace=page.workspace, first_name=cleaned["first_name"],
            last_name=cleaned["last_name"], email=email,
            phone=cleaned.get("phone", ""), person_type="lead",
            email_opt_in=False, sms_opt_in=False,
        )
    assigned_agent = page.assigned_agent if page.assigned_agent_id and Membership.objects.filter(workspace=page.workspace, user_id=page.assigned_agent_id, is_active=True, user__is_active=True).exists() else None
    lead = Lead.objects.create(
        workspace=page.workspace,
        person=person,
        assigned_agent=assigned_agent,
        lead_type=TEMPLATE_TO_LEAD_TYPE[page.template],
        status="new",
        source="landing_page:" + str(page.pk),
        next_step="Follow up on landing page inquiry",
        notes=cleaned.get("message", ""),
    )
    Task.objects.create(
        workspace=page.workspace,
        related_person=person,
        assigned_agent=assigned_agent,
        title="Follow up: " + page.title,
        priority="high",
        description="New landing page inquiry, lead #" + str(lead.pk),
    )
    return lead
