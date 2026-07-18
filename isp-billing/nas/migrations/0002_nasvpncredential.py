from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='NasVpnCredential',
            fields=[
                ('nas', models.OneToOneField(
                    db_column='nas_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='vpn',
                    serialize=False,
                    to='nas.nas',
                )),
                ('vpn_username', models.CharField(max_length=64, unique=True)),
                ('vpn_password', models.CharField(max_length=128)),
                ('remote_address', models.CharField(max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'nas_vpn_credentials',
                'managed': False,
            },
        ),
    ]
