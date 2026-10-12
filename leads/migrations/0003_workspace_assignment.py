from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial"), ("leads", "0002_alter_lead_options_lead_next_step_lead_referred_by_and_more")]
    operations = [
        migrations.AddField(
            model_name="lead",
            name="workspace",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="leads", to="accounts.workspace"),
        ),
        migrations.AddField(
            model_name="lead",
            name="assigned_agent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_crm_leads", to="auth.user"),
        ),
    ]
