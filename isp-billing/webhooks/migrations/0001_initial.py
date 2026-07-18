from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentGatewayEvent',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('payment_type', models.CharField(choices=[('platform', 'Platform'), ('subscriber', 'Subscriber')], max_length=10)),
                ('payment_id', models.BigIntegerField()),
                ('gateway', models.CharField(max_length=32)),
                ('event_type', models.CharField(blank=True, max_length=64, null=True)),
                ('status_reported', models.CharField(blank=True, max_length=32, null=True)),
                ('payload', models.JSONField()),
                ('received_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'payment_gateway_events',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PaymentRefund',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('payment_type', models.CharField(choices=[('platform', 'Platform'), ('subscriber', 'Subscriber')], max_length=10)),
                ('payment_id', models.BigIntegerField()),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('reason', models.CharField(blank=True, max_length=255, null=True)),
                ('gateway_refund_id', models.CharField(blank=True, max_length=128, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'payment_refunds',
                'managed': False,
            },
        ),
    ]
