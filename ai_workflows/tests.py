from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import Workspace, Membership
from people.models import Person
from leads.models import Lead
from .models import AgentRecommendation, TransactionCase

class AgentWorkbenchTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("reviewer", password="example")
        self.outsider = User.objects.create_user("outside", password="example")
        self.workspace = Workspace.objects.create(name="Review", kind="solo")
        self.other = Workspace.objects.create(name="Other", kind="brokerage")
        Membership.objects.create(user=self.user, workspace=self.workspace, role="owner")
        Membership.objects.create(user=self.outsider, workspace=self.other, role="owner")
        person = Person.objects.create(workspace=self.workspace, first_name="Dana", last_name="Client", email="dana@example.test", person_type="lead")
        other_person = Person.objects.create(workspace=self.other, first_name="Other", last_name="Client", email="other@example.test", person_type="lead")
        self.lead = Lead.objects.create(workspace=self.workspace, person=person, lead_type="buyer")
        self.foreign_lead = Lead.objects.create(workspace=self.other, person=other_person, lead_type="buyer")
        self.case = TransactionCase.objects.create(workspace=self.workspace, lead=self.lead, title="Oak Street", closing_date=timezone.localdate() + timedelta(days=3))
        self.foreign_case = TransactionCase.objects.create(workspace=self.other, lead=self.foreign_lead, title="Private Deal")
        self.client.force_login(self.user)

    def test_workbench_scopes_leads_and_transactions(self):
        response = self.client.get(reverse("ai_workbench"))
        self.assertContains(response, "Oak Street")
        self.assertNotContains(response, "Private Deal")
        self.assertNotContains(response, "Other Client")

    def test_cannot_review_foreign_lead_or_transaction(self):
        response = self.client.post(reverse("ai_review_lead", args=[self.foreign_lead.pk]))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse("ai_review_transaction", args=[self.foreign_case.pk]))
        self.assertEqual(response.status_code, 404)

    def test_transaction_form_rejects_foreign_lead(self):
        response = self.client.post(reverse("ai_create_transaction"), {"title":"Incorrect", "stage":"under_contract", "lead":self.foreign_lead.pk})
        self.assertEqual(response.status_code, 200)
        self.assertIn("lead", response.context["form"].errors)
        self.assertFalse(TransactionCase.objects.filter(title="Incorrect").exists())

    def test_proposals_require_explicit_review_and_do_not_create_tasks(self):
        from tasks.models import Task
        count = Task.objects.count()
        response = self.client.post(reverse("ai_review_transaction", args=[self.case.pk]))
        self.assertEqual(response.status_code, 302)
        proposal = AgentRecommendation.objects.get(workspace=self.workspace, title="Closing approaching")
        self.assertEqual(proposal.status, "proposed")
        self.assertEqual(Task.objects.count(), count)
        self.assertEqual(self.client.get(reverse("ai_review_transaction", args=[self.case.pk])).status_code, 405)
        self.client.post(reverse("ai_update_recommendation", args=[proposal.pk, "acknowledged"]))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, "acknowledged")

    def test_no_invented_deadline_when_missing(self):
        self.case.closing_date = None
        self.case.save(update_fields=["closing_date"])
        self.client.post(reverse("ai_review_transaction", args=[self.case.pk]))
        self.assertTrue(AgentRecommendation.objects.filter(transaction=self.case, title="Closing date unconfirmed").exists())

    def test_create_transaction_with_own_lead(self):
        response = self.client.post(reverse("ai_create_transaction"), {"title":"New contract", "stage":"under_contract", "lead":self.lead.pk})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TransactionCase.objects.filter(workspace=self.workspace, lead=self.lead, title="New contract").exists())

    def test_lead_proposals_identify_lead_and_refresh_without_duplicate_active_items(self):
        self.client.post(reverse("ai_review_lead", args=[self.lead.pk]))
        first = AgentRecommendation.objects.filter(lead=self.lead, status="proposed").count()
        self.assertGreater(first, 0)
        response = self.client.get(reverse("ai_workbench"))
        self.assertContains(response, "Dana Client (Lead #")
        self.client.post(reverse("ai_review_lead", args=[self.lead.pk]))
        self.assertEqual(AgentRecommendation.objects.filter(lead=self.lead, status="proposed").count(), first)
        self.assertEqual(AgentRecommendation.objects.filter(lead=self.lead).count(), first * 2)

    def test_acknowledged_recommendations_not_in_active_queue(self):
        self.client.post(reverse("ai_review_lead", args=[self.lead.pk]))
        item = AgentRecommendation.objects.filter(lead=self.lead, status="proposed").first()
        self.client.post(reverse("ai_update_recommendation", args=[item.pk, "acknowledged"]))
        response = self.client.get(reverse("ai_workbench"))
        self.assertNotContains(response, item.explanation)
