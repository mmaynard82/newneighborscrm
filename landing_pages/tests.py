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

    def test_wordpress_draft_endpoint_uses_query_rest_route(self):
        from .wordpress import WORDPRESS_PAGES_API
        self.assertEqual(WORDPRESS_PAGES_API, "https://newneighborsinc.com/?rest_route=/wp/v2/pages")

    def test_wordpress_update_uses_query_rest_route_with_page_id(self):
        import os
        from unittest.mock import patch, MagicMock
        from .wordpress import sync_draft
        self.page.wordpress_page_id = 123
        fake = MagicMock()
        fake.__enter__.return_value = fake
        fake.read.return_value = b'{"id":123,"status":"draft","link":"https://newneighborsinc.com/?page_id=123"}'
        with patch.dict(os.environ, {"NEWNEIGHBORS_WP_USERNAME": "test", "NEWNEIGHBORS_WP_APP_PASSWORD": "test"}):
            with patch("landing_pages.wordpress.urlopen", return_value=fake) as opened:
                sync_draft(self.page)
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url, "https://newneighborsinc.com/?rest_route=/wp/v2/pages/123")
        self.assertEqual(request.get_method(), "POST")


class PublicLandingInquiryTests(TestCase):
    def setUp(self):
        self.workspace = Workspace.objects.create(name="Public workspace", kind="solo")
        self.other = Workspace.objects.create(name="Other workspace", kind="solo")
        self.page = LandingPage.objects.create(
            workspace=self.workspace, title="Valuation", slug="public-valuation",
            headline="How much?", template="valuation",
        )
        self.url = reverse("landing_pages_public_inquiry", args=[self.page.public_form_token])
        self.payload = {
            "first_name": "Pat", "last_name": "Buyer",
            "email": "pat@example.test", "phone": "5551230000",
        }

    def test_public_form_requires_no_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.assertEqual(self.client.get("/landing-pages/inquiry/not-a-token/").status_code, 404)

    def test_submission_creates_correct_workspace_records(self):
        from leads.models import Lead
        from tasks.models import Task
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 200)
        lead = Lead.objects.get(source="landing_page:" + str(self.page.pk))
        self.assertEqual(lead.workspace_id, self.workspace.pk)
        self.assertEqual(lead.person.workspace_id, self.workspace.pk)
        self.assertEqual(Task.objects.filter(workspace=self.workspace, related_person=lead.person).count(), 1)
        self.assertFalse(Lead.objects.filter(workspace=self.other).exists())

    def test_honeypot_does_not_create_leads(self):
        from leads.models import Lead
        self.assertEqual(self.client.post(self.url, dict(self.payload, website="spam.example")).status_code, 200)
        self.assertFalse(Lead.objects.exists())

    def test_invalid_form_does_not_create_leads(self):
        from leads.models import Lead
        response = self.client.post(self.url, dict(self.payload, email="not-an-email"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Lead.objects.exists())

    def test_wordpress_draft_includes_public_form_link(self):
        import os
        import json
        from unittest.mock import patch, MagicMock
        from .wordpress import sync_draft
        fake = MagicMock()
        fake.__enter__.return_value = fake
        fake.read.return_value = b'{"id":55,"status":"draft","link":"https://newneighborsinc.com/?page_id=55"}'
        with patch.dict(os.environ, {"NEWNEIGHBORS_WP_USERNAME": "test", "NEWNEIGHBORS_WP_APP_PASSWORD": "test"}):
            with patch("landing_pages.wordpress.urlopen", return_value=fake) as opened:
                sync_draft(self.page)
        payload = json.loads(opened.call_args.args[0].data)
        self.assertEqual(payload["status"], "draft")
        self.assertIn(self.page.public_form_token, payload["content"])
        self.assertIn("newneighborscrm.onrender.com", payload["content"])


class WordPressPublishTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("pubowner", password="example")
        self.agent = get_user_model().objects.create_user("pubagent", password="example")
        self.outsider = get_user_model().objects.create_user("puboutside", password="example")
        self.workspace = Workspace.objects.create(name="Publish workspace", kind="brokerage")
        self.other = Workspace.objects.create(name="Other publisher", kind="solo")
        Membership.objects.create(user=self.owner, workspace=self.workspace, role="owner")
        Membership.objects.create(user=self.agent, workspace=self.workspace, role="agent")
        Membership.objects.create(user=self.outsider, workspace=self.other, role="owner")
        self.page = LandingPage.objects.create(
            workspace=self.workspace, title="Publish example",
            slug="publish-example", headline="Hello", wordpress_page_id=799,
        )
        self.url = reverse("landing_pages_wordpress_publish", args=[self.page.id])

    def test_get_is_confirmation_only(self):
        from unittest.mock import patch
        self.client.force_login(self.owner)
        with patch("landing_pages.views.publish_existing_draft") as publish:
            self.assertContains(self.client.get(self.url), "Confirm: Publish to WordPress")
            publish.assert_not_called()

    def test_agent_and_outsider_cannot_publish(self):
        from unittest.mock import patch
        with patch("landing_pages.views.publish_existing_draft") as publish:
            self.client.force_login(self.agent)
            self.assertEqual(self.client.post(self.url, {"confirm": "publish"}).status_code, 403)
            self.client.force_login(self.outsider)
            self.assertEqual(self.client.post(self.url, {"confirm": "publish"}).status_code, 404)
            publish.assert_not_called()

    def test_post_requires_explicit_confirmation(self):
        from unittest.mock import patch
        self.client.force_login(self.owner)
        with patch("landing_pages.views.publish_existing_draft") as publish:
            self.assertEqual(self.client.post(self.url, {}).status_code, 400)
            publish.assert_not_called()

    def test_success_renders_confirmation(self):
        from unittest.mock import patch
        self.client.force_login(self.owner)
        with patch("landing_pages.views.publish_existing_draft") as publish:
            response = self.client.post(self.url, {"confirm": "publish"})
            self.assertContains(response, "SUCCESS: WordPress confirmed")
            publish.assert_called_once_with(self.page)

    def test_wordpress_rejection_does_not_mark_published(self):
        from unittest.mock import patch
        self.client.force_login(self.owner)
        with patch("landing_pages.views.publish_existing_draft", side_effect=RuntimeError("rejected")):
            response = self.client.post(self.url, {"confirm": "publish"})
            self.assertContains(response, "FAILED: Publication was not confirmed", status_code=502)
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "draft")

    def test_wordpress_api_confirms_before_local_publish(self):
        from unittest.mock import patch, MagicMock
        import os
        from .wordpress import publish_existing_draft
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = b'{"status":"publish","id":799,"link":"https://newneighborsinc.com/sample/"}'
        with patch.dict(os.environ, {"NEWNEIGHBORS_WP_USERNAME": "test", "NEWNEIGHBORS_WP_APP_PASSWORD": "test"}):
            with patch("landing_pages.wordpress.urlopen", return_value=mock_response) as opened:
                publish_existing_draft(self.page)
        request = opened.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertIn("rest_route=/wp/v2/pages/799", request.full_url)
        self.assertIn(b'"status": "publish"', request.data)
        self.page.refresh_from_db()
        self.assertEqual(self.page.status, "published")

    def test_draft_sync_cannot_unpublish_live_page(self):
        from .wordpress import sync_draft
        from unittest.mock import patch
        self.page.status = "published"
        self.page.save(update_fields=["status"])
        with patch("landing_pages.wordpress.urlopen") as opened:
            with self.assertRaisesRegex(RuntimeError, "Published pages cannot"):
                sync_draft(self.page)
            opened.assert_not_called()


class AssignedAgentAndStatsTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("agent_owner", password="example")
        self.agent = get_user_model().objects.create_user("routed_agent", password="example")
        self.outside = get_user_model().objects.create_user("outside_agent", password="example")
        self.workspace = Workspace.objects.create(name="Agent routing", kind="brokerage")
        self.other = Workspace.objects.create(name="Other agent routing", kind="solo")
        Membership.objects.create(user=self.owner, workspace=self.workspace, role="owner")
        Membership.objects.create(user=self.agent, workspace=self.workspace, role="agent")
        Membership.objects.create(user=self.outside, workspace=self.other, role="agent")
        self.page = LandingPage.objects.create(workspace=self.workspace, title="Agent page", slug="agent-page", headline="Agent", assigned_agent=self.agent)
        self.client.force_login(self.owner)

    def test_form_cannot_assign_agent_from_another_workspace(self):
        response = self.client.post(reverse("landing_pages_edit", args=[self.page.pk]), {
            "title": "Agent page", "slug": "agent-page", "template": "custom",
            "headline": "Agent", "description": "", "button_text": "Contact Us",
            "assigned_agent": self.outside.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("assigned_agent", response.context["form"].errors)
        self.page.refresh_from_db()
        self.assertEqual(self.page.assigned_agent, self.agent)

    def test_public_inquiry_assigns_lead_and_task(self):
        from leads.models import Lead
        from tasks.models import Task
        response = self.client.post(reverse("landing_pages_public_inquiry", args=[self.page.public_form_token]), {
            "first_name": "Example", "last_name": "Customer", "email": "assigned@example.test",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.get(source="landing_page:" + str(self.page.id)).assigned_agent, self.agent)
        self.assertEqual(Task.objects.get(title="Follow up: Agent page").assigned_agent, self.agent)

    def test_inactive_agent_receives_no_assignment(self):
        from leads.models import Lead
        Membership.objects.filter(user=self.agent, workspace=self.workspace).update(is_active=False)
        self.client.post(reverse("landing_pages_public_inquiry", args=[self.page.public_form_token]), {
            "first_name": "Example", "last_name": "Second", "email": "inactive@example.test",
        })
        self.assertIsNone(Lead.objects.get(source="landing_page:" + str(self.page.id)).assigned_agent)

    def test_list_shows_per_page_submission_count(self):
        from leads.models import Lead
        self.client.post(reverse("landing_pages_public_inquiry", args=[self.page.public_form_token]), {
            "first_name": "Example", "last_name": "Third", "email": "stats@example.test",
        })
        response = self.client.get(reverse("landing_pages_list"))
        self.assertContains(response, "1 inquiries")
        self.assertContains(response, "routed_agent")


class LandingPageVisualDesignTests(TestCase):
    def test_wordpress_content_uses_theme_blocks_and_escapes_editor_input(self):
        from .design import render_wordpress_content
        workspace = Workspace.objects.create(name="Styling", kind="solo")
        page = LandingPage.objects.create(
            workspace=workspace, title="Test", slug="styled",
            headline="<script>alert(1)</script>", description="Helping owners",
            template="valuation", button_text="Get started",
        )
        content = render_wordpress_content(page, "https://example.test/inquiry/?a=1&b=2")
        self.assertIn("wp:group", content)
        self.assertIn("wp:columns", content)
        self.assertIn("wp:button", content)
        self.assertIn("&lt;script&gt;", content)
        self.assertNotIn("<script>", content)
        self.assertIn("a=1&amp;b=2", content)

    def test_public_form_contains_branding_and_valid_fields(self):
        workspace = Workspace.objects.create(name="Public styling", kind="solo")
        page = LandingPage.objects.create(
            workspace=workspace, title="Public test", slug="public-style", headline="Let's talk",
        )
        response = self.client.get(reverse("landing_pages_public_inquiry", args=[page.public_form_token]))
        self.assertContains(response, "NEW NEIGHBORS")
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')


class LandingPageCRMDesignTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ui_user", password="example")
        self.workspace = Workspace.objects.create(name="UI workspace", kind="solo")
        Membership.objects.create(user=self.user, workspace=self.workspace, role="owner")
        self.client.force_login(self.user)

    def test_landing_list_uses_crm_navigation(self):
        response = self.client.get(reverse("landing_pages_list"))
        self.assertContains(response, "CRM Platform")
        self.assertContains(response, 'href="/pipeline/"')
        self.assertContains(response, 'href="/landing-pages/"')
        self.assertContains(response, "Create Landing Page")

    def test_landing_creator_uses_crm_layout_and_preserves_fields(self):
        response = self.client.get(reverse("landing_pages_create"))
        self.assertContains(response, "CRM Platform")
        self.assertContains(response, 'name="headline"')
        self.assertContains(response, 'name="assigned_agent"')
        self.assertContains(response, "Save Draft")
