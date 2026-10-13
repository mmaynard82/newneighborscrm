from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("landing_pages", "0002_public_form_token"),
    ]
    operations = [
        migrations.AddField(
            model_name="landingpage",
            name="assigned_agent",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assigned_landing_pages", to=settings.AUTH_USER_MODEL),
        ),
    ]
