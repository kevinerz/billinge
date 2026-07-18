from django.db import models

from tenants.models import Tenant
from billing.models import ServicePlan
from accounts.models import User


class VoucherBatch(models.Model):
    """Metadata satu batch voucher hotspot yang digenerate sekaligus (bukan
    kredensial RADIUS-nya sendiri — itu ada di radcheck/radusergroup, dibuat
    lewat vouchers/radius.py saat batch ini dibuat, lihat views.py). Batch
    bersifat immutable setelah dibuat (tidak ada updated_at) — kalau
    salah, hapus batch-nya (lihat perform_destroy di views.py yang juga
    membersihkan kredensial RADIUS terkait) lalu buat batch baru."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='voucher_batches')
    service_plan = models.ForeignKey(
        ServicePlan, db_column='service_plan_id', on_delete=models.PROTECT, null=True, blank=True,
    )
    batch_code = models.CharField(max_length=32)
    quantity = models.PositiveIntegerField()
    price_each = models.DecimalField(max_digits=14, decimal_places=2)
    generated_by_user = models.ForeignKey(
        User, db_column='generated_by_user_id', on_delete=models.SET_NULL, null=True, blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voucher_batches'
        managed = False  # tabel sudah ada dari sql/008_tenant_billing.sql
        unique_together = [('tenant', 'batch_code')]

    def __str__(self):
        return f'{self.batch_code} ({self.tenant.slug})'


class Voucher(models.Model):
    STATUS_CHOICES = [
        ('unused', 'Unused'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]

    id = models.BigAutoField(primary_key=True)
    batch = models.ForeignKey(VoucherBatch, db_column='batch_id', on_delete=models.CASCADE, related_name='vouchers')
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='vouchers')
    username = models.CharField(max_length=64)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unused')
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vouchers'
        managed = False  # tabel sudah ada dari sql/014_reporting_extras.sql
        unique_together = [('tenant', 'username')]

    def __str__(self):
        return f'{self.username} ({self.status})'
