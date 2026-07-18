from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsSuperAdminOnly, IsSuperAdminOrTenantAdmin, scope_queryset_to_tenant

from .models import (
    PlatformPlan, TenantSubscription, PlatformInvoice, PlatformPayment,
    ServicePlan, SubscriberSubscription, SubscriberInvoice, SubscriberPayment,
)
from .serializers import (
    PlatformPlanSerializer, TenantSubscriptionSerializer, PlatformInvoiceSerializer, PlatformPaymentSerializer,
    ServicePlanSerializer, SubscriberSubscriptionSerializer, SubscriberInvoiceSerializer, SubscriberPaymentSerializer,
)


# --- Platform -> Tenant ---

class PlatformPlanViewSet(viewsets.ModelViewSet):
    """Katalog paket yang dijual platform ke tenant. Semua yang login boleh
    lihat (biar tenant tahu paket apa saja yang tersedia); cuma super_admin
    yang boleh bikin/ubah/hapus paketnya."""
    queryset = PlatformPlan.objects.all().order_by('price')
    serializer_class = PlatformPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOnly()]
        return [IsAuthenticated()]


class TenantSubscriptionViewSet(viewsets.ModelViewSet):
    """Tenant sedang pakai paket apa. Tenant cuma boleh lihat punya sendiri;
    yang boleh bikin/ubah cuma super_admin (ini keputusan bisnis platform,
    bukan self-service tenant)."""
    serializer_class = TenantSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TenantSubscription.objects.select_related('platform_plan', 'tenant').order_by('-current_period_end')
        return scope_queryset_to_tenant(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOnly()]
        return [IsAuthenticated()]


class PlatformInvoiceViewSet(viewsets.ModelViewSet):
    """Invoice platform ke tenant. Tenant lihat punya sendiri saja; cuma
    super_admin yang boleh bikin/ubah (nanti bisa digantikan billing engine
    otomatis)."""
    serializer_class = PlatformInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PlatformInvoice.objects.prefetch_related('items').order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOnly()]
        return [IsAuthenticated()]


class PlatformPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — pembayaran dicatat lewat webhook gateway, bukan lewat API
    manual ini. Tenant lihat punya sendiri saja."""
    serializer_class = PlatformPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PlatformPayment.objects.order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)


# --- Tenant -> Pelanggannya ---

class ServicePlanViewSet(viewsets.ModelViewSet):
    """Katalog paket layanan tenant buat pelanggannya sendiri. tenant_admin
    boleh kelola paket tenant-nya sendiri; tenant_staff cuma boleh lihat."""
    serializer_class = ServicePlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = ServicePlan.objects.all().order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOrTenantAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'super_admin':
            serializer.save()
        else:
            serializer.save(tenant_id=user.tenant_id)


class SubscriberSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriberSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SubscriberSubscription.objects.select_related('service_plan').order_by('-current_period_end')
        return scope_queryset_to_tenant(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOrTenantAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'super_admin':
            serializer.save()
        else:
            serializer.save(tenant_id=user.tenant_id)


class SubscriberInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriberInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SubscriberInvoice.objects.order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperAdminOrTenantAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'super_admin':
            serializer.save()
        else:
            serializer.save(tenant_id=user.tenant_id)


class SubscriberPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — sama seperti PlatformPaymentViewSet, dicatat lewat webhook."""
    serializer_class = SubscriberPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SubscriberPayment.objects.order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)
