from django.db import models

from tenants.models import Tenant


class TenantSubscriber(models.Model):
    """Pelanggan milik satu tenant (ISP). Model minimal dulu — cuma buat jadi
    referensi FK dari billing (subscriber_subscriptions, subscriber_invoices).
    API CRUD lengkap buat data pelanggan menyusul terpisah."""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    IDENTITY_CHOICES = [('ktp', 'KTP'), ('other', 'Other')]

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='subscribers')
    username = models.CharField(max_length=64)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    identity_type = models.CharField(max_length=10, choices=IDENTITY_CHOICES, default='ktp')
    identity_number = models.CharField(max_length=32, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    install_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    install_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenant_subscribers'
        managed = False

    def __str__(self):
        return f'{self.username} ({self.tenant.slug})'
