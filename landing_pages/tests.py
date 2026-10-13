from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from accounts.models import Membership, Workspace
from .models import LandingPage


class LandingPageIsolationTests(TestCase):
    def test_workspace_lists_only_own_pages(self):
        user = get_user_model().objects.create_user("publisher", password="example")
        own = Workspace.objects.create(name="Own", kind="solo")
        other = Workspace.objects.create(name="Other", kind="brokerage")
        Membership.objects.create(user=user, workspace=own)
        LandingPage.objects.create(workspace=own, title="Own Page", slug="own", headline="Own")
        foreign = LandingPage.objects.create(workspace=other, title="Other Page", slug="other", headline="Other")
        self.client.force_login(user)
        response = self.client.get(reverse("landing_pages_list"))
        self.assertContains(response, "Own Page")
        self.assertNotContains(response, "Other Page")
        response = self.client.get(reverse("landing_pages_edit", args=[foreign.id]))
        self.assertEqual(response.status_code, 404)

    def test_form_cannot_override_workspace_or_publishing_status(self):
        user = get_user_model().objects.create_user("author", password="example")
        own = Workspace.objects.create(name="Own", kind="solo")
        other = Workspace.objects.create(name="Other", kind="brokerage")
        Membership.objects.create(user=user, workspace=own)
        self.client.force_login(user)
        response = self.client.post(reverse("landing_pages_create"), {
            "title": "New Page", "slug": "new-page", "template": "valuation",
            "headline": "Find out", "description": "", "button_text": "Contact us",
            "workspace": other.id, "status": "published",
        })
        self.assertEqual(response.status_code, 302)
        page = LandingPage.objects.get(slug="new-page")
        self.assertEqual(page.workspace, own)
        self.assertEqual(page.status, "draft")

    def test_preview_creates_lead_and_followup_for_own_workspace(self):
        from leads.models import Lead
        from tasks.models import Task
        user = get_user_model().objects.create_user("preview_agent", password="example")
        workspace = Workspace.objects.create(name="Preview", kind="solo")
        Membership.objects.create(user=user, workspace=workspace)
        page = LandingPage.objects.create(workspace=workspace, title="Valuation", slug="valuation", headline="Home value", template="valuation")
        self.client.force_login(user)
        response = self.client.post(reverse("landing_pages_preview", args=[page.id]), {
            "first_name": "Sample", "last_name": "Person",
            "email": "sample@example.test", "phone": "5551112222", "message": "Interested",
        })
        self.assertEqual(response.status_code, 200)
        lead = Lead.objects.get(source="landing_page:" + str(page.id))
        self.assertEqual(lead.workspace_id, workspace.id)
        self.assertEqual(lead.person.workspace_id, workspace.id)
        self.assertEqual(lead.lead_type, "seller")
        self.assertEqual(Task.objects.filter(workspace=workspace, related_person=lead.person).count(), 1)

    def test_foreign_workspace_cannot_preview_or_submit(self):
        from leads.models import Lead
        user = get_user_model().objects.create_user("preview_other", password="example")
        own = Workspace.objects.create(name="Own preview", kind="solo")
        other = Workspace.objects.create(name="Other preview", kind="brokerage")
        Membership.objects.create(user=user, workspace=own)
        page = LandingPage.objects.create(workspace=other, title="Other valuation", slug="other-valuation", headline="Home value")
        self.client.force_login(user)
        response = self.client.post(reverse("landing_pages_preview", args=[page.id]), {
            "first_name": "Sample", "last_name": "Person", "email": "sample@example.test",
        })
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Lead.objects.filter(source="landing_page:" + str(page.id)).exists())

    def test_repeat_inquiry_reuses_contact_in_workspace(self):
        from people.models import Person
        user = get_user_model().objects.create_user("preview_repeat", password="example")
        workspace = Workspace.objects.create(name="Repeat preview", kind="solo")
        Membership.objects.create(user=user, workspace=workspace)
        page = LandingPage.objects.create(workspace=workspace, title="Repeat", slug="repeat", headline="Repeat")
        self.client.force_login(user)
        payload = {"first_name": "Sample", "last_name": "Person", "email": "Sample@Example.test"}
        self.client.post(reverse("landing_pages_preview", args=[page.id]), payload)
        self.client.post(reverse("landing_pages_preview", args=[page.id]), payload)
        self.assertEqual(Person.objects.filter(workspace=workspace, email__iexact=payload["email"]).count(), 1)


class WordPressDraftSyncTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("wpowner", password="example")
        self.agent = get_user_model().objects.create_user("wpagent", password="example")
        self.other = get_user_model().objects.create_user("wpother", password="example")
        self.workspace = Workspace.objects.create(name="WP", kind="brokerage")
        self.foreign = Workspace.objects.create(name="Foreign WP", kind="solo")
        Membership.objects.create(user=self.owner, workspace=self.workspace, role="owner")
        Membership.objects.create(user=self.agent, workspace=self.workspace, role="agent")
        Membership.objects.create(user=self.other, workspace=self.foreign, role="owner")
        self.page = LandingPage.objects.create(workspace=self.workspace, title="Draft", slug="wp-draft", headline="Draft")

    def test_get_cannot_trigger_sync(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("landing_pages_wordpress_sync", args=[self.page.id]))
        self.assertEqual(response.status_code, 405)

    def test_agent_cannot_sync(self):
        from unittest.mock import patch
        self.client.force_login(self.agent)
        with patch("landing_pages.views.sync_draft") as sync:
            response = self.client.post(reverse("landing_pages_wordpress_sync", args=[self.page.id]))
            self.assertEqual(response.status_code, 403)
            sync.assert_not_called()

    def test_other_workspace_cannot_sync(self):
        from unittest.mock import patch
        self.client.force_login(self.other)
        with patch("landing_pages.views.sync_draft") as sync:
            response = self.client.post(reverse("landing_pages_wordpress_sync", args=[self.page.id]))
            self.assertEqual(response.status_code, 404)
            sync.assert_not_called()

    def test_owner_sync_uses_draft_function(self):
        from unittest.mock import patch
        self.client.force_login(self.owner)
        with patch("landing_pages.views.sync_draft") as sync:
            response = self.client.post(reverse("landing_pages_wordpress_sync", args=[self.page.id]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "SUCCESS: WordPress confirmed")
            sync.assert_called_once_with(self.page)

    def test_success_message_appears_after_draft_sync(self):
        from unittest.mock import patch
        user = get_user_model().objects.create_user("message_owner", password="example")
        workspace = Workspace.objects.create(name="Message CRM", kind="solo")
        Membership.objects.create(user=user, workspace=workspace, role="owner")
        page = LandingPage.objects.create(workspace=workspace, title="Example", slug="example", headline="Example")
        self.client.force_login(user)
        with patch("landing_pages.views.sync_draft"):
            response = self.client.post(reverse("landing_pages_wordpress_sync", args=[page.id]), follow=True)
        self.assertContains(response, "SUCCESS: WordPress confirmed")

    def test_failure_message_appears_after_draft_sync(self):
        from unittest.mock import patch
        user = get_user_model().objects.create_user("message_owner2", password="example")
        workspace = Workspace.objects.create(name="Message CRM 2", kind="solo")
        Membership.objects.create(user=user, workspace=workspace, role="owner")
        page = LandingPage.objects.create(workspace=workspace, title="Example", slug="example", headline="Example")
        self.client.force_login(user)
        with patch("landing_pages.views.sync_draft", side_effect=RuntimeError("Simulated failure")):
            response = self.client.post(reverse("landing_pages_wordpress_sync", args=[page.id]), follow=True)
        self.assertContains(response, "FAILED: WordPress did not confirm the draft.", status_code=502)

    def test_unexpected_wordpress_exception_shows_safe_failure(self):
        from unittest.mock import patch
        self.client.force_login(self.owner)
        with patch("landing_pages.views.sync_draft", side_effect=ValueError("invalid remote JSON")):
            response = self.client.post(reverse("landing_pages_wordpress_sync", args=[self.page.id]))
        self.assertContains(response, "FAILED: WordPress did not confirm the draft.", status_code=502)
        self.assertContains(response, "An unexpected server error occurred.", status_code=502)
        self.assertNotContains(response, "invalid remote JSON", status_code=502)

    def test_non_json_wordpress_response_is_handled(self):
        from unittest.mock import patch
        from .wordpress import sync_draft
        from unittest.mock import MagicMock
        import os
        fake_response = MagicMock()
        fake_response.headers.get.return_value = "text/html"
        fake_response.geturl.return_value = "https://newneighborsinc.com/wp-json/wp/v2/pages"
        fake_response.status = 200
        fake_response.read.return_value = b"<html>Not an API response</html>"
        fake_response.__enter__.return_value = fake_response
        with patch.dict(os.environ, {"NEWNEIGHBORS_WP_USERNAME": "test", "NEWNEIGHBORS_WP_APP_PASSWORD": "test"}):
            with patch("landing_pages.wordpress.urlopen", return_value=fake_response):
                with self.assertRaisesRegex(RuntimeError, "non-JSON response"):
                    sync_draft(self.page)
