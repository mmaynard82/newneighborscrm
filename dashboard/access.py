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
    "other",
]


def user_has_full_crm_access(user):
    if user.is_superuser:
        return True

    return user.groups.filter(name=FULL_ACCESS_GROUP_NAME).exists()


def get_allowed_lead_type_keys(user):
    """
    Superusers and CRM Full Access users can see all lead types.

    Real Estate Only users can only see real estate lead types.

    Any user without a specific CRM access group defaults to Real Estate Only
    for safety.
    """

    all_lead_types = [value for value, label in Lead.LEAD_TYPES]

    if user_has_full_crm_access(user):
        return all_lead_types

    if user.groups.filter(name=REAL_ESTATE_ONLY_GROUP_NAME).exists():
        return REAL_ESTATE_ONLY_LEAD_TYPES

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

    return queryset.filter(lead_type__in=allowed_keys)


def user_can_view_lead(user, lead):
    allowed_keys = get_allowed_lead_type_keys(user)

    return lead.lead_type in allowed_keys


def require_lead_access(user, lead):
    if not user_can_view_lead(user, lead):
        raise Http404("Lead not found.")

    return lead