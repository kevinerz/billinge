from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsSuperAdminOrOwnTenant, IsSuperAdminOrTenantAdmin, scope_queryset_to_tenant

from .models import TenantSubscriber
from .serializers import TenantSubscriberSerializer


class TenantSubscriberViewSet(viewsets.ModelViewSet):
    """
    Data pelanggan tenant. Beda dari service-plans (yang dianggap "billing",
    dibatasi tenant_admin ke atas): tenant_staff BOLEH kelola data pelanggan
    (nama, alamat, kontak) — cuma menghapus pelanggan yang dibatasi ke
    tenant_admin/super_admin, karena itu aksi yang lebih sensitif.
    """
    serializer_class = TenantSubscriberSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrOwnTenant]

    def get_queryset(self):
        qs = TenantSubscriber.objects.select_related('tenant').order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated(), IsSuperAdminOrTenantAdmin()]
        return [IsAuthenticated(), IsSuperAdminOrOwnTenant()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'super_admin':
            serializer.save()
        else:
            serializer.save(tenant_id=user.tenant_id)
