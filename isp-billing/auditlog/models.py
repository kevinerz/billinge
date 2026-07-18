from django.db import models


class AuditLog(models.Model):
    """Jejak audit generik untuk aksi dashboard/API (tenant.created,
    nas.added, invoice.paid, dst). tenant_id NULL = aksi level platform
    (mis. super_admin bikin tenant baru); user_id NULL = aksi dari script,
    bukan user yang login. tenant_id/user_id sengaja BigIntegerField polos
    (bukan ForeignKey) supaya auditlog tidak perlu import tenants/accounts —
    banyak app lain yang akan import auditlog.log_action(), jadi arah
    dependency-nya harus satu arah."""

    id = models.BigAutoField(primary_key=True)
    tenant_id = models.BigIntegerField(null=True, blank=True)
    user_id = models.BigIntegerField(null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=64, null=True, blank=True)
    entity_id = models.BigIntegerField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        managed = False  # tabel sudah ada dari sql/009_audit_log.sql

    def __str__(self):
        return f'{self.action} (tenant={self.tenant_id}, user={self.user_id})'
