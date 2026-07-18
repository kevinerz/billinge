from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
        ('billing', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoucherBatch',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('batch_code', models.CharField(max_length=32)),
                ('quantity', models.PositiveIntegerField()),
                ('price_each', models.DecimalField(decimal_places=2, max_digits=14)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tenant', models.ForeignKey(db_column='tenant_id', on_delete=django.db.models.deletion.CASCADE, related_name='voucher_batches', to='tenants.tenant')),
                ('service_plan', models.ForeignKey(blank=True, db_column='service_plan_id', null=True, on_delete=django.db.models.deletion.PROTECT, to='billing.serviceplan')),
                ('generated_by_user', models.ForeignKey(blank=True, db_column='generated_by_user_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.user')),
            ],
            options={
                'db_table': 'voucher_batches',
                'managed': False,
                'unique_together': {('tenant', 'batch_code')},
            },
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=64)),
                ('status', models.CharField(choices=[('unused', 'Unused'), ('active', 'Active'), ('expired', 'Expired')], default='unused', max_length=10)),
                ('redeemed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('batch', models.ForeignKey(db_column='batch_id', on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='vouchers.voucherbatch')),
                ('tenant', models.ForeignKey(db_column='tenant_id', on_delete=django.db.models.deletion.CASCADE, related_name='vouchers', to='tenants.tenant')),
            ],
            options={
                'db_table': 'vouchers',
                'managed': False,
                'unique_together': {('tenant', 'username')},
            },
        ),
    ]
