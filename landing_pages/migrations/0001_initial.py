from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="LandingPage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=150)),
                ("template", models.CharField(choices=[("valuation", "Home Valuation"), ("probate", "Probate"), ("property_management", "Property Management"), ("downsizing", "Downsizing"), ("open_house", "Open House"), ("custom", "Custom")], default="custom", max_length=40)),
                ("headline", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("button_text", models.CharField(default="Contact Us", max_length=80)),
                ("wordpress_page_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("wordpress_url", models.URLField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="landing_pages", to="accounts.workspace")),
            ],
        ),
        migrations.AddConstraint(model_name="landingpage", constraint=models.UniqueConstraint(fields=("workspace", "slug"), name="unique_landing_page_workspace_slug")),
    ]
