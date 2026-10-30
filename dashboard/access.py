from accounts.access import visible_records, require_record_access
from django.http import Http404

from leads.models import Lead


FULL_ACCESS_GROUP_NAME = "CRM Full Access"
REAL_ESTATE_ONLY_GROUP_NAME = "Real Estate Only"


RESTRICTED_SERVICE_LEAD_TYPES = [
    "property_management",
    "home_management",
    "flat_fee_listing",
]


REAL_ESTATE_ONLY_LEAD_TYPES = [
    "buyer",
    "seller",
    "investor",
    "referral",
    "probate_estate",
    "downsizing",
    "flat_fee_listing",
    "other",
]


def user_has_full_crm_access(user):
    if user.is_superuser:
        return True

    return user.groups.filter(name=FULL_ACCESS_GROUP_NAME).exists()


def get_allowed_lead_type_keys(user):
    """Sales-only CRM; legacy service leads remain stored for administrative export."""
    return REAL_ESTATE_ONLY_LEAD_TYPES


def get_allowed_lead_type_choices(user):
    allowed_keys = get_allowed_lead_type_keys(user)

    return [
        (value, label)
        for value, label in Lead.LEAD_TYPES
        if value in allowed_keys
    ]


def filter_leads_for_user(queryset, user):
    allowed_keys = get_allowed_lead_type_keys(user)

    return visible_records(queryset, user).filter(lead_type__in=allowed_keys)


def user_can_view_lead(user, lead):
    allowed_keys = get_allowed_lead_type_keys(user)

    return lead.lead_type in allowed_keys and lead.workspace_id is not None and visible_records(Lead.objects.filter(pk=lead.pk), user).exists()


def require_lead_access(user, lead):
    if not user_can_view_lead(user, lead):
        raise Http404("Lead not found.")

    return lead