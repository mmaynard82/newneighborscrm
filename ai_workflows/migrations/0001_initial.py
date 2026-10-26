from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("accounts", "0001_initial"),
        ("leads", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(name="TransactionCase", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("title", models.CharField(max_length=200)),
            ("stage", models.CharField(max_length=30, choices=[("under_contract","Under contract"),("due_diligence","Due diligence"),("financing","Financing"),("clear_to_close","Clear to close"),("closed","Closed"),("cancelled","Cancelled")], default="under_contract")),
            ("inspection_deadline", models.DateField(blank=True, null=True)),
            ("financing_deadline", models.DateField(blank=True, null=True)),
            ("closing_date", models.DateField(blank=True, null=True)),
            ("notes", models.TextField(blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transaction_cases", to="accounts.workspace")),
            ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="transaction_cases", to="leads.lead")),
        ]),
        migrations.CreateModel(name="AgentRecommendation", fields=[
            ("id", models.BigAutoField(primary_key=True, serialize=False)),
            ("kind", models.CharField(max_length=20, choices=[("lead","Lead review"),("transaction","Transaction review")])),
            ("title", models.CharField(max_length=250)),
            ("explanation", models.TextField()),
            ("status", models.CharField(max_length=20, choices=[("proposed","Proposed"),("acknowledged","Acknowledged"),("dismissed","Dismissed")], default="proposed")),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ai_recommendations", to="accounts.workspace")),
            ("lead", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="leads.lead")),
            ("transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="ai_workflows.transactioncase")),
            ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ]),
    ]
