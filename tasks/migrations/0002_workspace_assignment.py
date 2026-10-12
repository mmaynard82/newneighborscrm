from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial"), ("tasks", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="task",
            name="workspace",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="tasks", to="accounts.workspace"),
        ),
        migrations.AddField(
            model_name="task",
            name="assigned_agent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_crm_tasks", to="auth.user"),
        ),
    ]
