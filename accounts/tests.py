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


class IsolationTests(TestCase):
    def test_leads_hidden_from_other_workspace_and_unassigned(self):
        from people.models import Person
        from leads.models import Lead
        from dashboard.access import filter_leads_for_user, require_lead_access
        from django.http import Http404

        first = get_user_model().objects.create_user("agent_one", password="example")
        second = get_user_model().objects.create_user("agent_two", password="example")
        one = Workspace.objects.create(name="One", kind=Workspace.SOLO)
        two = Workspace.objects.create(name="Two", kind=Workspace.BROKERAGE)
        Membership.objects.create(user=first, workspace=one)
        Membership.objects.create(user=second, workspace=two)
        person = Person.objects.create(first_name="Sample")
        own = Lead.objects.create(person=person, lead_type="buyer", workspace=one)
        other = Lead.objects.create(person=person, lead_type="seller", workspace=two)
        legacy = Lead.objects.create(person=person, lead_type="buyer")
        ids = set(filter_leads_for_user(Lead.objects.all(), first).values_list("id", flat=True))
        self.assertEqual(ids, {own.pk})
        with self.assertRaises(Http404):
            require_lead_access(first, other)
        with self.assertRaises(Http404):
            require_lead_access(first, legacy)
