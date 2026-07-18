from django.db import models

from tenants.models import Tenant


class Nas(models.Model):
    """Router Mikrotik tenant. Ini tabel yang DIBACA LANGSUNG oleh
    FreeRADIUS (read_clients=yes) buat resolusi tenant dari IP NAS — lihat
    freeradius-isp/docs/architecture.md. id sengaja AutoField (int biasa,
    bukan BigAutoField) karena itu skema asli bawaan FreeRADIUS, bukan
    konvensi bigint-unsigned yang kita pakai di tabel-tabel baru."""

    TYPE_CHOICES = [('other', 'Other'), ('mikrotik', 'Mikrotik')]

    id = models.AutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='nas_list')
    nasname = models.CharField(max_length=128, unique=True)  # IP router — kunci resolusi tenant di FreeRADIUS
    shortname = models.CharField(max_length=32, null=True, blank=True)
    type = models.CharField(max_length=30, default='other')
    ports = models.IntegerField(null=True, blank=True)
    secret = models.CharField(max_length=60)
    server = models.CharField(max_length=64, null=True, blank=True)
    community = models.CharField(max_length=50, null=True, blank=True)
    description = models.CharField(max_length=200, default='RADIUS Client')
    last_contact_at = models.DateTimeField(null=True, blank=True)  # diupdate FreeRADIUS sendiri, bukan lewat API

    class Meta:
        db_table = 'nas'
        managed = False

    def __str__(self):
        return f'{self.nasname} ({self.tenant.slug})'
