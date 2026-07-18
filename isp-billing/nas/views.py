import secrets as secrets_lib  # nama beda dari field model `secret`

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from auditlog.helpers import log_action
from common.permissions import IsSuperAdminOrOwnTenant, IsSuperAdminOrTenantAdmin, scope_queryset_to_tenant

from .models import Nas
from .serializers import NasSerializer


class NasViewSet(viewsets.ModelViewSet):
    """
    Manajemen router Mikrotik. SENGAJA dibatasi tenant_admin ke atas untuk
    SEMUA aksi termasuk lihat (bukan cuma tulis) — beda dari subscribers.
    Alasan: (1) nas.secret itu kredensial RADIUS asli, (2) salah konfigurasi
    NAS bisa bikin SELURUH pelanggan tenant itu terputus internetnya
    sekaligus — risiko lebih tinggi dari sekadar data pelanggan biasa,
    jadi tenant_staff tidak diberi akses sama sekali ke endpoint ini.
    """
    serializer_class = NasSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin, IsSuperAdminOrOwnTenant]

    def get_queryset(self):
        qs = Nas.objects.select_related('tenant').order_by('-id')
        return scope_queryset_to_tenant(qs, self.request.user)

    def perform_create(self, serializer):
        # Secret digenerate baru & acak tiap NAS, tidak pernah dari input
        # client — satu router bocor tidak akan membocorkan secret router lain.
        generated_secret = secrets_lib.token_urlsafe(24)
        user = self.request.user
        if user.role == 'super_admin':
            nas = serializer.save(secret=generated_secret)
        else:
            nas = serializer.save(tenant_id=user.tenant_id, secret=generated_secret)
        log_action(
            self.request, 'nas.created', entity_type='nas', entity_id=nas.id,
            metadata={'nasname': nas.nasname, 'shortname': nas.shortname}, tenant_id=nas.tenant_id,
        )
