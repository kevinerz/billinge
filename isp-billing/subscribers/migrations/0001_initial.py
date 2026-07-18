from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantSubscriber',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=64)),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('phone', models.CharField(blank=True, max_length=32, null=True)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('identity_type', models.CharField(choices=[('ktp', 'KTP'), ('other', 'Other')], default='ktp', max_length=10)),
                ('identity_number', models.CharField(blank=True, max_length=32, null=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('install_lat', models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ('install_lng', models.DecimalField(blank=True, decimal_places=7, max_digits=10, null=True)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('terminated', 'Terminated')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenant', models.ForeignKey(
                    db_column='tenant_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subscribers',
                    to='tenants.tenant',
                )),
            ],
            options={
                'db_table': 'tenant_subscribers',
                'managed': False,
            },
        ),
    ]
