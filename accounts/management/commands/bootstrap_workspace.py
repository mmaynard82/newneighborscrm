import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import Workspace, Membership


class Command(BaseCommand):
    help = "Provision the initial CRM workspace and owner using environment configuration."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        username = os.environ.get("CRM_BOOTSTRAP_USERNAME", "").strip()
        workspace_name = os.environ.get("CRM_BOOTSTRAP_WORKSPACE", "").strip()
        kind = os.environ.get("CRM_BOOTSTRAP_KIND", "brokerage").strip()
        if not username or not workspace_name:
            self.stdout.write("Workspace bootstrap not requested; skipping.")
            return
        if kind not in (Workspace.SOLO, Workspace.BROKERAGE):
            raise CommandError("CRM_BOOTSTRAP_KIND must be solo or brokerage.")
        user = get_user_model().objects.filter(username=username, is_active=True, is_superuser=True).first()
        if user is None:
            raise CommandError("Bootstrap user must be an existing active superuser.")
        existing = Workspace.objects.filter(memberships__user=user, memberships__is_active=True).distinct()
        if existing.exists():
            if existing.count() != 1 or existing.first().name != workspace_name or existing.first().kind != kind:
                raise CommandError("An active workspace already exists; review it manually rather than reassigning users.")
            self.stdout.write(self.style.SUCCESS("Workspace already configured; no changes made."))
            return
        workspace = Workspace.objects.filter(name=workspace_name, kind=kind).first()
        if workspace is not None:
            raise CommandError("Workspace name already exists; refusing to attach automatically.")
        workspace = Workspace.objects.create(name=workspace_name, kind=kind)
        Membership.objects.create(workspace=workspace, user=user, role=Membership.OWNER, is_active=True)
        self.stdout.write(self.style.SUCCESS("Workspace and owner membership created."))
