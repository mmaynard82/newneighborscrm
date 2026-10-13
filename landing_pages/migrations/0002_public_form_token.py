from django.db import migrations, models
import landing_pages.models


class Migration(migrations.Migration):
    dependencies = [("landing_pages", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="landingpage",
            name="public_form_token",
            field=models.CharField(max_length=64, null=True, editable=False),
        ),
        migrations.RunPython(
            lambda apps, schema_editor: [
                apps.get_model("landing_pages", "LandingPage").objects.filter(pk=pk).update(
                    public_form_token=landing_pages.models.new_form_token()
                )
                for pk in apps.get_model("landing_pages", "LandingPage").objects.values_list("pk", flat=True)
            ],
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="landingpage",
            name="public_form_token",
            field=models.CharField(max_length=64, unique=True, default=landing_pages.models.new_form_token, editable=False),
        ),
    ]
