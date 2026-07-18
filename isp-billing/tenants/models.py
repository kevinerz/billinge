from django.db import models


class Tenant(models.Model):
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]

    id = models.BigAutoField(primary_key=True)
    slug = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants'
        managed = False  # tabel sudah ada dari sql/002_tenants.sql

    def __str__(self):
        return self.name


class TenantBillingProfile(models.Model):
    tenant = models.OneToOneField(
        Tenant, primary_key=True, db_column='tenant_id',
        on_delete=models.CASCADE, related_name='billing_profile',
    )
    legal_name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=32, null=True, blank=True)
    billing_email = models.CharField(max_length=255, null=True, blank=True)
    billing_phone = models.CharField(max_length=32, null=True, blank=True)
    billing_address = models.CharField(max_length=500, null=True, blank=True)
    pic_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenant_billing_profiles'
        managed = False  # tabel sudah ada dari sql/011_tenant_billing_profile.sql
