from django import forms
from .models import TransactionCase, BrokerageSignatureTemplate, BrokerageContractPacket
from leads.models import Lead

class TransactionCaseForm(forms.ModelForm):
    class Meta:
        model = TransactionCase
        fields = ["title", "lead", "stage", "inspection_deadline", "financing_deadline", "closing_date", "notes"]
        widgets = {key: forms.DateInput(attrs={"type": "date"}) for key in ("inspection_deadline", "financing_deadline", "closing_date")}
    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = Lead.objects.filter(workspace=workspace) if workspace else Lead.objects.none()
        self.fields["lead"].required = False


class BrokerageSignatureTemplateForm(forms.ModelForm):
    class Meta:
        model = BrokerageSignatureTemplate
        fields = [
            "name", "provider_template_id", "buyer_role", "seller_role",
            "property_address_field", "purchase_price_field", "deposit_field",
            "closing_date_field", "additional_terms_field", "is_active",
        ]
    def clean(self):
        data = super().clean()
        if not data.get("buyer_role") and not data.get("seller_role"):
            raise forms.ValidationError("Configure at least one signer role matching the approved e-sign template.")
        if data.get("buyer_role") and data.get("buyer_role") == data.get("seller_role"):
            raise forms.ValidationError("Buyer and seller roles must be different.")
        return data


class BrokerageContractPacketForm(forms.ModelForm):
    class Meta:
        model = BrokerageContractPacket
        fields = [
            "template", "buyer_name", "buyer_email", "seller_name", "seller_email",
            "property_address", "purchase_price", "deposit", "closing_date", "additional_terms",
        ]
        widgets = {"closing_date": forms.DateInput(attrs={"type": "date"})}
    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        templates = BrokerageSignatureTemplate.objects.filter(workspace=workspace, is_active=True) if workspace else BrokerageSignatureTemplate.objects.none()
        if self.instance.pk and self.instance.template_id:
            templates = BrokerageSignatureTemplate.objects.filter(pk=self.instance.template_id, workspace=workspace) | templates
        self.fields["template"].queryset = templates.distinct()
    def clean(self):
        data = super().clean()
        template = data.get("template")
        if template:
            for role in ("buyer", "seller"):
                if getattr(template, role + "_role"):
                    if not data.get(role + "_name") or not data.get(role + "_email"):
                        self.add_error(role + "_email", "Name and email are required for this template's " + role + " signer.")
        return data


from django.contrib.auth import get_user_model
from accounts.models import Membership
from .models import FieldAppointment


class FieldAppointmentForm(forms.ModelForm):
    class Meta:
        model = FieldAppointment
        fields = ["event_type", "title", "lead", "transaction", "assigned_agent", "location", "starts_at", "ends_at", "notes", "status"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
    def __init__(self, *args, workspace=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lead"].queryset = Lead.objects.filter(workspace=workspace) if workspace else Lead.objects.none()
        self.fields["transaction"].queryset = TransactionCase.objects.filter(workspace=workspace) if workspace else TransactionCase.objects.none()
        allowed_ids = Membership.objects.filter(
            workspace=workspace, is_active=True, user__is_active=True,
        ).values_list("user_id", flat=True) if workspace else []
        self.fields["assigned_agent"].queryset = get_user_model().objects.filter(pk__in=allowed_ids)
        self.fields["assigned_agent"].required = False
        self.fields["starts_at"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["ends_at"].input_formats = ["%Y-%m-%dT%H:%M"]
    def clean(self):
        data = super().clean()
        start, end = data.get("starts_at"), data.get("ends_at")
        if start and end and end <= start:
            self.add_error("ends_at", "End time must be after start time.")
        return data
