from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsSuperAdminOrTenantAdmin

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — baris dibuat lewat log_action(), bukan lewat API."""
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = AuditLog.objects.all().order_by('-created_at')
        user = self.request.user
        if user.role == 'super_admin':
            return qs
        # tenant_admin cuma lihat log tenant-nya sendiri — baris dengan
        # tenant_id NULL (aksi level platform) sengaja tidak ikut ke-filter
        # masuk di sini karena NULL != tenant_id user manapun.
        return qs.filter(tenant_id=user.tenant_id)
