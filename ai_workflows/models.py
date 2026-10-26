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
