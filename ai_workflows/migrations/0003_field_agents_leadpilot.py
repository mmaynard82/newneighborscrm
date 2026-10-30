from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ai_workflows", "0002_brokerage_paperwork"),
    ]
    operations = [
        migrations.CreateModel(name="FieldAppointment", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("event_type", models.CharField(max_length=30, choices=[("buyer_consult","Buyer consultation"),("seller_consult","Listing appointment"),("showing","Property showing"),("open_house","Open house"),("offer","Offer review"),("inspection","Home inspection"),("appraisal","Appraisal"),("walkthrough","Final walk-through"),("closing","Closing"),("follow_up","Client follow-up")])),
            ("title", models.CharField(max_length=200)),
            ("location", models.CharField(blank=True, max_length=300)),
            ("starts_at", models.DateTimeField()),
            ("ends_at", models.DateTimeField(blank=True, null=True)),
            ("notes", models.TextField(blank=True)),
            ("status", models.CharField(max_length=20, choices=[("scheduled","Scheduled"),("completed","Completed"),("cancelled","Cancelled")], default="scheduled")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="field_appointments", to="accounts.workspace")),
            ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="field_appointments", to="leads.lead")),
            ("transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="field_appointments", to="ai_workflows.transactioncase")),
            ("assigned_agent", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="field_appointments", to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name="LeadPilotReview", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("reference", models.CharField(max_length=150, unique=True)),
            ("remote_run_id", models.CharField(blank=True, max_length=36)),
            ("status", models.CharField(default="pending", max_length=30)),
            ("result_json", models.JSONField(blank=True, default=dict)),
            ("error_message", models.CharField(blank=True, max_length=300)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="leadpilot_reviews", to="accounts.workspace")),
            ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="leadpilot_reviews", to="leads.lead")),
            ("transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="leadpilot_reviews", to="ai_workflows.transactioncase")),
            ("requested_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ]),
    ]
