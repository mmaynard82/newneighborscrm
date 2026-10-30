from django import forms
from .models import LandingPage
from accounts.models import Membership
from django.contrib.auth import get_user_model


class LandingPageForm(forms.ModelForm):
    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = Membership.objects.filter(
            workspace=workspace, is_active=True, user__is_active=True
        ).values_list("user_id", flat=True) if workspace else []
        self.fields["assigned_agent"].queryset = get_user_model().objects.filter(
            pk__in=allowed
        ).order_by("username")
        self.fields["assigned_agent"].required = False
        self.fields["assigned_agent"].label = "Route new inquiries to"
        self.fields["template"].choices = [choice for choice in self.fields["template"].choices if choice[0] != "property_management"]

    class Meta:
        model = LandingPage
        fields = ["title", "slug", "template", "headline", "description", "button_text", "assigned_agent"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class LandingInquiryForm(forms.Form):
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=50, required=False)
    message = forms.CharField(max_length=2000, required=False, widget=forms.Textarea)

    website = forms.CharField(max_length=200, required=False, widget=forms.HiddenInput)
