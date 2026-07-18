from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from auditlog.helpers import log_action
from common.permissions import IsSuperAdminOrTenantAdmin, scope_queryset_to_tenant

from .models import Tenant, TenantIntegration
from .permissions import IsSuperAdminOnly, IsSuperAdminOrOwnTenant
from .serializers import TenantSerializer, TenantIntegrationSerializer


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrOwnTenant]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'super_admin':
            return Tenant.objects.all().order_by('-created_at')
        # tenant_admin / tenant_staff cuma bisa lihat tenant miliknya sendiri
        return Tenant.objects.filter(id=user.tenant_id)

    def get_permissions(self):
        # Cuma super_admin yang boleh bikin tenant baru atau hapus tenant
        if self.action in ('create', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        tenant = serializer.save()
        log_action(
            self.request, 'tenant.created', entity_type='tenant', entity_id=tenant.id,
            metadata={'slug': tenant.slug, 'name': tenant.name}, tenant_id=tenant.id,
        )

    def perform_destroy(self, instance):
        log_action(
            self.request, 'tenant.deleted', entity_type='tenant', entity_id=instance.id,
            metadata={'slug': instance.slug}, tenant_id=instance.id,
        )
        instance.delete()


class TenantIntegrationViewSet(viewsets.ModelViewSet):
    """
    Konfigurasi kredensial gateway pembayaran/WA per tenant. Dibatasi
    tenant_admin ke atas (sama seperti NAS) — kredensial ini dipakai
    langsung oleh webhook untuk verifikasi signature, jadi tenant_staff
    tidak diberi akses.
    """
    serializer_class = TenantIntegrationSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = TenantIntegration.objects.select_related('tenant').order_by('-id')
        return scope_queryset_to_tenant(qs, self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'super_admin':
            integration = serializer.save()
        else:
            integration = serializer.save(tenant_id=user.tenant_id)
        log_action(
            self.request, 'tenant_integration.created', entity_type='tenant_integration', entity_id=integration.id,
            metadata={'integration_type': integration.integration_type, 'provider': integration.provider},
            tenant_id=integration.tenant_id,
        )
