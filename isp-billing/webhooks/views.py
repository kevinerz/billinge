import os

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import PlatformPayment, SubscriberPayment
from tenants.models import Tenant, TenantIntegration

from . import gateways
from .models import PaymentGatewayEvent, PaymentRefund

VALID_PROVIDERS = ('midtrans', 'xendit')

# Kredensial gateway MILIK PLATFORM SENDIRI (dipakai untuk platform_payments —
# platform menagih tenant). Beda dari TenantIntegration, yang menyimpan
# kredensial gateway MILIK TENANT (dipakai tenant menagih pelanggannya sendiri).
PLATFORM_GATEWAY_CREDENTIALS = {
    'midtrans': {'server_key': os.getenv('PLATFORM_MIDTRANS_SERVER_KEY', '')},
    'xendit': {'callback_token': os.getenv('PLATFORM_XENDIT_CALLBACK_TOKEN', '')},
}


def _apply_webhook(payment, payment_type, provider, payload, headers):
    """Logika bersama: log event, lalu terapkan transisi status forward-only.
    Selalu return (status_code, body) — dipakai kedua view di bawah."""
    raw_status = gateways.extract_raw_status(provider, payload)
    new_status = gateways.normalize_status(provider, raw_status)

    PaymentGatewayEvent.objects.create(
        payment_type=payment_type,
        payment_id=payment.id,
        gateway=provider,
        event_type=f'{provider}.{raw_status}' if raw_status else None,
        status_reported=raw_status,
        payload=payload,
    )

    if new_status is None:
        # Status yang belum kita kenal — sudah dicatat di atas untuk
        # investigasi, tapi tidak mengubah apa pun. Tetap 200 supaya
        # gateway tidak retry terus menerus.
        return 200, {'received': True, 'applied': False, 'reason': 'unrecognized_status'}

    if not gateways.should_apply_transition(payment.status, new_status):
        return 200, {'received': True, 'applied': False, 'reason': 'stale_or_out_of_order'}

    with transaction.atomic():
        payment.status = new_status
        txn_id = gateways.extract_transaction_id(provider, payload)
        if txn_id:
            payment.gateway_transaction_id = txn_id
        method = gateways.extract_payment_method(provider, payload)
        if method:
            payment.payment_method = method
        payment.raw_payload = payload
        if new_status == 'settlement' and not payment.paid_at:
            payment.paid_at = timezone.now()
        payment.save()

        if new_status == 'settlement':
            invoice = payment.invoice
            if invoice.status != 'paid':
                invoice.status = 'paid'
                invoice.paid_at = payment.paid_at
                invoice.save(update_fields=['status', 'paid_at', 'updated_at'])

        if new_status in gateways.POST_SETTLEMENT_STATUSES:
            PaymentRefund.objects.create(
                payment_type=payment_type,
                payment_id=payment.id,
                amount=payload.get('refund_amount') or payload.get('amount') or payment.amount,
                reason=f'{provider} reported {raw_status}',
                gateway_refund_id=payload.get('refund_id') or payload.get('id'),
                status='completed',
            )

    return 200, {'received': True, 'applied': True, 'status': new_status}


class PlatformPaymentWebhookView(APIView):
    """Webhook dari gateway PLATFORM (kredensial dari env, bukan per-tenant) —
    untuk platform_payments (platform menagih tenant sewa SaaS)."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, provider):
        provider = provider.lower()
        if provider not in VALID_PROVIDERS:
            return Response({'detail': 'Unknown provider'}, status=404)

        credentials = PLATFORM_GATEWAY_CREDENTIALS[provider]
        payload = request.data
        if not gateways.verify_signature(provider, payload, credentials, request.headers):
            return Response({'detail': 'Invalid signature'}, status=403)

        order_id = gateways.extract_order_id(provider, payload)
        if not order_id:
            return Response({'detail': 'Missing order id'}, status=400)

        payment = PlatformPayment.objects.filter(gateway=provider, gateway_order_id=order_id).first()
        if not payment:
            return Response({'detail': 'Payment not found for order id'}, status=404)

        status_code, body = _apply_webhook(payment, 'platform', provider, payload, request.headers)
        return Response(body, status=status_code)


class SubscriberPaymentWebhookView(APIView):
    """Webhook dari gateway MILIK TENANT (kredensial dari tenant_integrations,
    tenant diidentifikasi lewat slug di URL) — untuk subscriber_payments
    (tenant menagih pelanggannya sendiri). Tiap tenant daftarkan URL webhook
    ini di dashboard gateway-nya masing-masing, satu URL per tenant per
    provider, karena tiap tenant pakai akun gateway sendiri-sendiri."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, tenant_slug, provider):
        provider = provider.lower()
        if provider not in VALID_PROVIDERS:
            return Response({'detail': 'Unknown provider'}, status=404)

        tenant = get_object_or_404(Tenant, slug=tenant_slug)
        integration = TenantIntegration.objects.filter(
            tenant=tenant, integration_type='payment_gateway', provider=provider, is_active=True,
        ).first()
        if not integration:
            return Response({'detail': 'No active payment gateway integration for this tenant'}, status=404)

        payload = request.data
        if not gateways.verify_signature(provider, payload, integration.credentials, request.headers):
            return Response({'detail': 'Invalid signature'}, status=403)

        order_id = gateways.extract_order_id(provider, payload)
        if not order_id:
            return Response({'detail': 'Missing order id'}, status=400)

        payment = SubscriberPayment.objects.filter(
            gateway=provider, gateway_order_id=order_id, tenant=tenant,
        ).first()
        if not payment:
            return Response({'detail': 'Payment not found for order id'}, status=404)

        status_code, body = _apply_webhook(payment, 'subscriber', provider, payload, request.headers)
        return Response(body, status=status_code)
