from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from billing.models import PlatformPayment, SubscriberPayment
from common.permissions import IsSuperAdminOrTenantAdmin

from .models import PaymentGatewayEvent, PaymentRefund
from .serializers import PaymentGatewayEventSerializer, PaymentRefundSerializer


def _scope_polymorphic_payment_query(qs, user):
    """payment_gateway_events/payment_refunds tidak punya kolom tenant_id
    sendiri (polimorfik ke platform_payments ATAU subscriber_payments) —
    jadi scoping tenant harus lewat subquery ke dua tabel payment itu,
    beda dari scope_queryset_to_tenant() yang generik di common/permissions.py."""
    if user.role == 'super_admin':
        return qs
    platform_ids = PlatformPayment.objects.filter(tenant_id=user.tenant_id).values_list('id', flat=True)
    subscriber_ids = SubscriberPayment.objects.filter(tenant_id=user.tenant_id).values_list('id', flat=True)
    return qs.filter(
        Q(payment_type='platform', payment_id__in=platform_ids)
        | Q(payment_type='subscriber', payment_id__in=subscriber_ids)
    )


class PaymentGatewayEventViewSet(viewsets.ReadOnlyModelViewSet):
    """Jejak audit webhook — read-only, tidak ada create/update lewat API
    (event dibuat oleh webhooks/views.py, bukan dashboard)."""
    serializer_class = PaymentGatewayEventSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = PaymentGatewayEvent.objects.all().order_by('-received_at')
        return _scope_polymorphic_payment_query(qs, self.request.user)


class PaymentRefundViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — refund dibuat otomatis dari webhook, bukan dashboard."""
    serializer_class = PaymentRefundSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = PaymentRefund.objects.all().order_by('-created_at')
        return _scope_polymorphic_payment_query(qs, self.request.user)
