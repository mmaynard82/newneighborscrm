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


class BrokeragePaperworkTests(TestCase):
    def setUp(self):
        from .models import BrokerageSignatureTemplate, BrokerageContractPacket
        User = get_user_model()
        self.owner = User.objects.create_user("broker_owner", password="example")
        self.agent = User.objects.create_user("broker_agent", password="example")
        self.foreign = User.objects.create_user("broker_foreign", password="example")
        self.workspace = Workspace.objects.create(name="Brokerage Workspace", kind="brokerage")
        self.other = Workspace.objects.create(name="Other Brokerage", kind="brokerage")
        Membership.objects.create(user=self.owner, workspace=self.workspace, role="owner")
        Membership.objects.create(user=self.agent, workspace=self.workspace, role="agent")
        Membership.objects.create(user=self.foreign, workspace=self.other, role="owner")
        self.case = TransactionCase.objects.create(workspace=self.workspace, title="Main Street purchase")
        self.other_case = TransactionCase.objects.create(workspace=self.other, title="Private transaction")
        self.template = BrokerageSignatureTemplate.objects.create(
            workspace=self.workspace, name="Approved purchase agreement",
            provider_template_id="approved-template-id",
            buyer_role="Buyer", seller_role="Seller", property_address_field="PropertyAddress",
        )
        self.other_template = BrokerageSignatureTemplate.objects.create(
            workspace=self.other, name="Foreign Agreement",
            provider_template_id="private-id", buyer_role="Buyer",
        )
        self.packet = BrokerageContractPacket.objects.create(
            workspace=self.workspace, transaction=self.case, template=self.template,
            buyer_name="Alex Buyer", buyer_email="alex@example.test",
            seller_name="Sam Seller", seller_email="sam@example.test",
            property_address="22 Main Street", created_by=self.owner,
        )

    def test_agent_can_prepare_packet_but_cannot_send_or_register_template(self):
        self.client.force_login(self.agent)
        self.assertEqual(self.client.get(reverse("brokerage_new_paperwork_template")).status_code, 403)
        self.assertEqual(self.client.post(reverse("brokerage_send_contract_packet", args=[self.packet.pk]), {"confirmation":"send"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("brokerage_contract_packet", args=[self.packet.pk])).status_code, 200)

    def test_other_workspace_cannot_access_packet_or_transaction(self):
        self.client.force_login(self.foreign)
        self.assertEqual(self.client.get(reverse("brokerage_contract_packet", args=[self.packet.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("brokerage_new_contract_packet", args=[self.case.pk])).status_code, 404)

    def test_cannot_select_foreign_workspace_template(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("brokerage_new_contract_packet", args=[self.case.pk]), {
            "template": self.other_template.pk, "buyer_name": "Alex",
            "buyer_email": "alex@example.test", "property_address": "22 Main Street",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("template", response.context["form"].errors)

    def test_authorized_send_has_explicit_confirmation_and_one_provider_call(self):
        from unittest.mock import patch
        from .models import BrokerageContractPacket
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("brokerage_send_contract_packet", args=[self.packet.pk])).status_code, 200)
        with patch("ai_workflows.views.send_request", return_value=("signature-123", True)) as mocked:
            self.assertEqual(self.client.post(reverse("brokerage_send_contract_packet", args=[self.packet.pk]), {"confirmation":"wrong"}).status_code, 400)
            self.assertEqual(self.client.post(reverse("brokerage_send_contract_packet", args=[self.packet.pk]), {"confirmation":"send"}).status_code, 302)
            self.assertEqual(self.client.post(reverse("brokerage_send_contract_packet", args=[self.packet.pk]), {"confirmation":"send"}).status_code, 302)
            self.assertEqual(mocked.call_count, 1)
        self.packet.refresh_from_db()
        self.assertEqual(self.packet.provider_request_id, "signature-123")
        self.assertTrue(self.packet.sent_test_mode)
        self.assertEqual(self.packet.status, "sent")
        self.assertEqual(BrokerageContractPacket.objects.filter(pk=self.packet.pk).count(), 1)

    def test_provider_failure_preserves_unsent_draft(self):
        from unittest.mock import patch
        from .esign import SignatureSendError
        self.client.force_login(self.owner)
        with patch("ai_workflows.views.send_request", side_effect=SignatureSendError("No provider")):
            self.client.post(reverse("brokerage_send_contract_packet", args=[self.packet.pk]), {"confirmation":"send"})
        self.packet.refresh_from_db()
        self.assertEqual(self.packet.status, "draft")
        self.assertEqual(self.packet.provider_request_id, "")

    def test_provider_payload_uses_only_configured_custom_fields_and_recipient_roles(self):
        from .esign import prepare_request
        payload = prepare_request(self.packet)
        self.assertEqual(payload["template_ids"], ["approved-template-id"])
        self.assertEqual([s["role"] for s in payload["signers"]], ["Buyer", "Seller"])
        self.assertEqual(payload["custom_fields"], [{"name": "PropertyAddress", "value": "22 Main Street"}])

    def test_live_disabled_defaults_to_test_mode(self):
        import io
        import json
        from unittest.mock import patch
        from .esign import send_request
        encoded = json.dumps({"signature_request":{"signature_request_id":"test-id"}}).encode()
        with patch.dict("os.environ", {"DROPBOX_SIGN_API_KEY":"test-only", "CRM_ESIGN_LIVE_SEND_ENABLED":"false"}):
            with patch("ai_workflows.esign.urlopen", return_value=io.BytesIO(encoded)) as request:
                request_id, test_mode = send_request(self.packet)
                sent = json.loads(request.call_args.args[0].data)
        self.assertEqual(request_id, "test-id")
        self.assertTrue(test_mode)
        self.assertTrue(sent["test_mode"])

    def test_no_sales_management_records_are_deleted(self):
        from leads.models import Lead
        from people.models import Person
        from dashboard.access import get_allowed_lead_type_keys
        old_person = Person.objects.create(workspace=self.workspace, first_name="Legacy", last_name="Owner", person_type="lead")
        old = Lead.objects.create(workspace=self.workspace, person=old_person, lead_type="property_management")
        self.assertNotIn(old.lead_type, get_allowed_lead_type_keys(self.owner))
        self.assertTrue(Lead.objects.filter(pk=old.pk).exists())


class FieldAgentBridgeTests(TestCase):
    def setUp(self):
        from .models import FieldAppointment
        self.owner = get_user_model().objects.create_user("field_owner", password="test")
        self.other_user = get_user_model().objects.create_user("field_other", password="test")
        self.workspace = Workspace.objects.create(name="Field desk", kind="brokerage")
        self.other = Workspace.objects.create(name="Other field desk", kind="brokerage")
        Membership.objects.create(user=self.owner, workspace=self.workspace, role="owner")
        Membership.objects.create(user=self.other_user, workspace=self.other, role="agent")
        person = Person.objects.create(workspace=self.workspace, first_name="Avery", last_name="Buyer", email="avery@example.test", person_type="lead")
        foreign = Person.objects.create(workspace=self.other, first_name="Morgan", last_name="Seller", email="morgan@example.test", person_type="lead")
        self.lead = Lead.objects.create(workspace=self.workspace, person=person, lead_type="buyer", notes="Looking for a condo")
        self.foreign_lead = Lead.objects.create(workspace=self.other, person=foreign, lead_type="seller")
        self.case = TransactionCase.objects.create(workspace=self.workspace, title="Main Street contract", lead=self.lead)
        self.client.force_login(self.owner)

    def test_field_desk_has_showings_and_agent_team_actions(self):
        response = self.client.get(reverse("ai_workbench"))
        self.assertContains(response, "Agent Field Desk")
        self.assertContains(response, "Schedule showing")
        self.assertContains(response, "Ask LeadPilot AI")
        self.assertContains(response, "Offers")

    def test_appointment_cannot_use_foreign_client(self):
        from .models import FieldAppointment
        time = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("field_appointment_new"), {
            "title": "Buyer tour", "event_type": "showing", "starts_at": time,
            "lead": self.foreign_lead.pk, "status": "scheduled",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("lead", response.context["form"].errors)
        self.assertFalse(FieldAppointment.objects.filter(title="Buyer tour").exists())

    def test_valid_showing_appears_in_field_calendar(self):
        from .models import FieldAppointment
        time = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        response = self.client.post(reverse("field_appointment_new"), {
            "title": "Private condo tour", "event_type": "showing",
            "starts_at": time, "lead": self.lead.pk, "status": "scheduled",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FieldAppointment.objects.filter(workspace=self.workspace, title="Private condo tour").exists())
        self.assertContains(self.client.get(reverse("ai_workbench")), "Private condo tour")

    def test_unconfigured_bridge_creates_nonblocking_audit(self):
        from .models import LeadPilotReview
        from unittest.mock import patch
        with patch.dict("os.environ", {}, clear=True):
            response = self.client.post(reverse("leadpilot_start_lead", args=[self.lead.pk]))
        self.assertEqual(response.status_code, 302)
        review = LeadPilotReview.objects.get(lead=self.lead)
        self.assertEqual(review.status, "unavailable")
        self.assertFalse(review.remote_run_id)

    def test_client_cannot_start_foreign_lead_review(self):
        from .models import LeadPilotReview
        response = self.client.post(reverse("leadpilot_start_lead", args=[self.foreign_lead.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(LeadPilotReview.objects.exists())

    def test_leadpilot_result_requires_explicit_refresh_and_never_sends_message(self):
        from .models import LeadPilotReview
        from unittest.mock import patch
        from tasks.models import Task
        before = Task.objects.count()
        with patch("ai_workflows.views.start_review", return_value={"run_id":"0d97b1b3-1425-4e50-8ccb-5e2d9b9c1f6e","status":"queued"}):
            response = self.client.post(reverse("leadpilot_start_transaction", args=[self.case.pk]))
        self.assertEqual(response.status_code, 302)
        review = LeadPilotReview.objects.get(transaction=self.case)
        self.assertEqual(review.status, "queued")
        with patch("ai_workflows.views.check_review", return_value={"run_id":review.remote_run_id, "status":"awaiting_approval", "result":{"summary":"Verify financing dates"}}):
            response = self.client.post(reverse("leadpilot_refresh", args=[review.pk]))
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.result_json["summary"], "Verify financing dates")
        self.assertEqual(Task.objects.count(), before)

    def test_refresh_cannot_view_other_workspace_reviews(self):
        from .models import LeadPilotReview
        foreign = LeadPilotReview.objects.create(workspace=self.other, lead=self.foreign_lead, reference="foreign-review-123", remote_run_id="0d97b1b3-1425-4e50-8ccb-5e2d9b9c1f6e")
        self.assertEqual(self.client.post(reverse("leadpilot_refresh", args=[foreign.pk])).status_code, 404)
