from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("ai_workflows", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="BrokerageSignatureTemplate",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("provider_template_id", models.CharField(max_length=200)),
                ("buyer_role", models.CharField(blank=True, max_length=100)),
                ("seller_role", models.CharField(blank=True, max_length=100)),
                ("property_address_field", models.CharField(blank=True, max_length=100)),
                ("purchase_price_field", models.CharField(blank=True, max_length=100)),
                ("deposit_field", models.CharField(blank=True, max_length=100)),
                ("closing_date_field", models.CharField(blank=True, max_length=100)),
                ("additional_terms_field", models.CharField(blank=True, max_length=100)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="signature_templates", to="accounts.workspace")),
            ],
        ),
        migrations.CreateModel(
            name="BrokerageContractPacket",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("buyer_name", models.CharField(blank=True, max_length=200)),
                ("buyer_email", models.EmailField(blank=True, max_length=254)),
                ("seller_name", models.CharField(blank=True, max_length=200)),
                ("seller_email", models.EmailField(blank=True, max_length=254)),
                ("property_address", models.CharField(blank=True, max_length=300)),
                ("purchase_price", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("deposit", models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ("closing_date", models.DateField(blank=True, null=True)),
                ("additional_terms", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft","Draft"),("sent","Sent for signature")], default="draft", max_length=20)),
                ("provider_request_id", models.CharField(blank=True, max_length=200)),
                ("sent_test_mode", models.BooleanField(default=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_contract_packets", to=settings.AUTH_USER_MODEL)),
                ("template", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contract_packets", to="ai_workflows.brokeragesignaturetemplate")),
                ("transaction", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contract_packets", to="ai_workflows.transactioncase")),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="contract_packets", to="accounts.workspace")),
            ],
        ),
    ]
