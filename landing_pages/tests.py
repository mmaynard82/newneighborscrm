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
