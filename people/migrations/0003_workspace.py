from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial'), ('people', '0002_alter_person_options_person_do_not_contact_and_more')]
    operations = [migrations.AddField(model_name='person', name='workspace', field=models.ForeignKey(to='accounts.workspace', on_delete=django.db.models.deletion.PROTECT, related_name='people', null=True, blank=True))]
