from django import forms

from leads.models import Lead
from tags.models import Tag
from .models import Campaign


class CampaignForm(forms.ModelForm):
    audience_lead_type = forms.ChoiceField(
        choices=[("", "Any Lead Type")] + Lead.LEAD_TYPES,
        required=False,
        label="Audience Lead Type",
    )

    audience_lead_status = forms.ChoiceField(
        choices=[("", "Any Lead Status")] + Lead.LEAD_STATUSES,
        required=False,
        label="Audience Lead Status",
    )

    audience_tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        label="Audience Tag",
    )

    class Meta:
        model = Campaign
        fields = [
            "name",
            "campaign_type",
            "status",
            "audience_lead_type",
            "audience_lead_status",
            "audience_tag",
            "subject",
            "message",
            "notes",
        ]

        widgets = {
            "message": forms.Textarea(attrs={"rows": 7}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }