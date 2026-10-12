from django.http import Http404
from .models import Membership


def workspace_ids_for(user):
    if not user.is_authenticated:
        return []
    return Membership.objects.filter(user=user, is_active=True).values_list('workspace_id', flat=True)


def visible_records(queryset, user):
    return queryset.filter(workspace_id__in=workspace_ids_for(user))


def require_record_access(user, record):
    if not record.workspace_id or not Membership.objects.filter(workspace_id=record.workspace_id, user=user, is_active=True).exists():
        raise Http404('Record not found')
    return record


def single_workspace_for(user):
    """Require an unambiguous active workspace until switching UI exists."""
    from .models import Workspace
    ids = list(workspace_ids_for(user)[:2])
    if len(ids) != 1:
        raise Http404('Choose a workspace before accessing CRM records')
    return Workspace.objects.get(pk=ids[0])


def scope_crm_form(form, user):
    """Restrict related-record choices to memberships before validation/rendering."""
    from people.models import Person
    from properties.models import Property
    from leads.models import Lead
    from tags.models import Tag
    for field in form.fields.values():
        queryset = getattr(field, 'queryset', None)
        if queryset is None:
            continue
        model = queryset.model
        if model in (Person, Property):
            field.queryset = visible_records(queryset, user)
        elif model is Lead:
            field.queryset = visible_records(queryset, user)
    return form
