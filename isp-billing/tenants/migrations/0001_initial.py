from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('slug', models.CharField(max_length=64, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('trial', 'Trial'), ('active', 'Active'), ('suspended', 'Suspended')], default='trial', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'tenants',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TenantBillingProfile',
            fields=[
                ('tenant', models.OneToOneField(
                    db_column='tenant_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='billing_profile',
                    serialize=False,
                    to='tenants.tenant',
                )),
                ('legal_name', models.CharField(max_length=255)),
                ('tax_id', models.CharField(blank=True, max_length=32, null=True)),
                ('billing_email', models.CharField(blank=True, max_length=255, null=True)),
                ('billing_phone', models.CharField(blank=True, max_length=32, null=True)),
                ('billing_address', models.CharField(blank=True, max_length=500, null=True)),
                ('pic_name', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'tenant_billing_profiles',
                'managed': False,
            },
        ),
    ]
