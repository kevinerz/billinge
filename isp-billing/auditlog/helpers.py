"""log_action() — dipanggil dari app lain (tenants, nas, accounts, ...) di
titik-titik aksi yang sensitif (create/delete, ganti role, dst). Sengaja
dipisah dari models.py/views.py biar app lain cukup import satu fungsi ini
tanpa perlu tahu bentuk model AuditLog."""
from .models import AuditLog


def log_action(request, action, entity_type=None, entity_id=None, metadata=None, tenant_id=None):
    user = getattr(request, 'user', None)
    authenticated = bool(user and user.is_authenticated)
    if tenant_id is None and authenticated:
        tenant_id = user.tenant_id
    AuditLog.objects.create(
        tenant_id=tenant_id,
        user_id=user.id if authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
    )


def log_system_action(action, entity_type=None, entity_id=None, metadata=None, tenant_id=None):
    """Sama seperti log_action(), buat aksi yang BUKAN dipicu request user
    yang login — dijalankan dari Celery task/cron (billing engine, dst).
    user_id selalu NULL, sesuai desain audit_logs (lihat sql/009_audit_log.sql)."""
    AuditLog.objects.create(
        tenant_id=tenant_id,
        user_id=None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
    )
