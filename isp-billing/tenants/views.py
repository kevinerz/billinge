from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Tenant
from .permissions import IsSuperAdminOnly, IsSuperAdminOrOwnTenant
from .serializers import TenantSerializer


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
