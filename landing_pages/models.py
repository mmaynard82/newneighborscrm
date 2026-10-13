import secrets
from django.db import models


def new_form_token():
    return secrets.token_urlsafe(32)


class LandingPage(models.Model):
    TEMPLATES = [
        ("valuation", "Home Valuation"),
        ("probate", "Probate"),
        ("property_management", "Property Management"),
        ("downsizing", "Downsizing"),
        ("open_house", "Open House"),
        ("custom", "Custom"),
    ]
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.PROTECT, related_name="landing_pages")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=150)
    template = models.CharField(max_length=40, choices=TEMPLATES, default="custom")
    headline = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    button_text = models.CharField(max_length=80, default="Contact Us")
    public_form_token = models.CharField(max_length=64, unique=True, default=new_form_token, editable=False)
    wordpress_page_id = models.PositiveBigIntegerField(null=True, blank=True)
    wordpress_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("published", "Published")], default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["workspace", "slug"], name="unique_landing_page_workspace_slug")]

    def __str__(self):
        return self.title
