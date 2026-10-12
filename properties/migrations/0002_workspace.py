from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial'), ('properties', '0001_initial')]
    operations = [migrations.AddField(model_name='property', name='workspace', field=models.ForeignKey(to='accounts.workspace', on_delete=django.db.models.deletion.PROTECT, related_name='properties', null=True, blank=True))]
