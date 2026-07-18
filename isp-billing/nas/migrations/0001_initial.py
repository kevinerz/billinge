from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Nas',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('nasname', models.CharField(max_length=128, unique=True)),
                ('shortname', models.CharField(blank=True, max_length=32, null=True)),
                ('type', models.CharField(default='other', max_length=30)),
                ('ports', models.IntegerField(blank=True, null=True)),
                ('secret', models.CharField(max_length=60)),
                ('server', models.CharField(blank=True, max_length=64, null=True)),
                ('community', models.CharField(blank=True, max_length=50, null=True)),
                ('description', models.CharField(default='RADIUS Client', max_length=200)),
                ('last_contact_at', models.DateTimeField(blank=True, null=True)),
                ('tenant', models.ForeignKey(
                    db_column='tenant_id',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='nas_list',
                    to='tenants.tenant',
                )),
            ],
            options={
                'db_table': 'nas',
                'managed': False,
            },
        ),
    ]
