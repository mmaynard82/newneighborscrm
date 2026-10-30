from django.conf import settings
from django.db import models

class TransactionCase(models.Model):
    id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.PROTECT, related_name="transaction_cases")
    lead = models.ForeignKey("leads.Lead", on_delete=models.SET_NULL, null=True, blank=True, related_name="transaction_cases")
    title = models.CharField(max_length=200)
    stage = models.CharField(max_length=30, choices=[("under_contract","Under contract"),("due_diligence","Due diligence"),("financing","Financing"),("clear_to_close","Clear to close"),("closed","Closed"),("cancelled","Cancelled")], default="under_contract")
    inspection_deadline = models.DateField(blank=True, null=True)
    financing_deadline = models.DateField(blank=True, null=True)
    closing_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AgentRecommendation(models.Model):
    id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.PROTECT, related_name="ai_recommendations")
    kind = models.CharField(max_length=20, choices=[("lead","Lead review"),("transaction","Transaction review")])
    lead = models.ForeignKey("leads.Lead", on_delete=models.CASCADE, null=True, blank=True)
    transaction = models.ForeignKey(TransactionCase, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=250)
    explanation = models.TextField()
    status = models.CharField(max_length=20, choices=[("proposed","Proposed"),("acknowledged","Acknowledged"),("dismissed","Dismissed")], default="proposed")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BrokerageSignatureTemplate(models.Model):
    """Reference to brokerage-approved forms already configured at Dropbox Sign."""
    id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.PROTECT, related_name="signature_templates")
    name = models.CharField(max_length=200)
    provider_template_id = models.CharField(max_length=200)
    buyer_role = models.CharField(max_length=100, blank=True)
    seller_role = models.CharField(max_length=100, blank=True)
    property_address_field = models.CharField(max_length=100, blank=True)
    purchase_price_field = models.CharField(max_length=100, blank=True)
    deposit_field = models.CharField(max_length=100, blank=True)
    closing_date_field = models.CharField(max_length=100, blank=True)
    additional_terms_field = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class BrokerageContractPacket(models.Model):
    """Approved-form preparation and signature request audit record; not a signed contract."""
    id = models.BigAutoField(primary_key=True)
    workspace = models.ForeignKey("accounts.Workspace", on_delete=models.PROTECT, related_name="contract_packets")
    transaction = models.ForeignKey(TransactionCase, on_delete=models.PROTECT, related_name="contract_packets")
    template = models.ForeignKey(BrokerageSignatureTemplate, on_delete=models.PROTECT, related_name="contract_packets")
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_email = models.EmailField(blank=True)
    seller_name = models.CharField(max_length=200, blank=True)
    seller_email = models.EmailField(blank=True)
    property_address = models.CharField(max_length=300, blank=True)
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    deposit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    additional_terms = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[("draft", "Draft"), ("sent", "Sent for signature")], default="draft")
    provider_request_id = models.CharField(max_length=200, blank=True)
    sent_test_mode = models.BooleanField(default=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_contract_packets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.template.name + " / " + self.transaction.title
