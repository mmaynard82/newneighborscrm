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
