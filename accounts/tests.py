from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from .models import Membership, Workspace


class WorkspaceTests(TestCase):
    def test_solo_and_brokerage_have_distinct_memberships(self):
        user = get_user_model().objects.create_user("testagent", password="example")
        solo = Workspace.objects.create(name="Solo", kind=Workspace.SOLO)
        brokerage = Workspace.objects.create(name="Brokerage", kind=Workspace.BROKERAGE)
        Membership.objects.create(user=user, workspace=solo, role=Membership.OWNER)
        Membership.objects.create(user=user, workspace=brokerage, role=Membership.AGENT)
        self.assertEqual(user.crm_memberships.count(), 2)

    def test_duplicate_membership_rejected(self):
        user = get_user_model().objects.create_user("testagent", password="example")
        workspace = Workspace.objects.create(name="Brokerage", kind=Workspace.BROKERAGE)
        Membership.objects.create(user=user, workspace=workspace)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membership.objects.create(user=user, workspace=workspace)
