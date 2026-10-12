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
