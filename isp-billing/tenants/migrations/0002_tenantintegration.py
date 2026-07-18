from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantIntegration',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('integration_type', models.CharField(choices=[('payment_gateway', 'Payment gateway'), ('whatsapp', 'WhatsApp'), ('sms', 'SMS'), ('email', 'Email')], max_length=20)),
                ('provider', models.CharField(max_length=64)),
                ('credentials', models.JSONField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(db_column='tenant_id', on_delete=django.db.models.deletion.CASCADE, related_name='integrations', to='tenants.tenant')),
            ],
            options={
                'db_table': 'tenant_integrations',
                'managed': False,
                'unique_together': {('tenant', 'integration_type')},
            },
        ),
    ]
