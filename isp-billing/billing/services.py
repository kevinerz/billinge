"""Efek samping REAL-TIME saat sebuah invoice lunas (dipanggil dari
webhooks/views.py saat status pembayaran jadi 'settlement') — majukan
periode langganan & pulihkan tenant/subscriber yang sempat disuspend
billing engine (billing/tasks.py). Sengaja real-time, bukan nunggu
jadwal harian berikutnya, supaya akses pulih secepat mungkin setelah
bayar."""
from auditlog.helpers import log_system_action


def advance_subscription_on_payment(payment_type, invoice):
    subscription = invoice.subscription
    if subscription is None:
        return

    subscription.current_period_start = invoice.period_start
    subscription.current_period_end = invoice.period_end
    subscription.status = 'active'
    subscription.save(update_fields=['current_period_start', 'current_period_end', 'status', 'updated_at'])

    if payment_type == 'platform':
        tenant = invoice.tenant
        if tenant.status == 'suspended':
            tenant.status = 'active'
            tenant.save(update_fields=['status', 'updated_at'])
            log_system_action(
                'tenant.auto_reactivated', entity_type='tenant', entity_id=tenant.id,
                metadata={'reason': 'platform_invoice_paid', 'invoice_id': invoice.id}, tenant_id=tenant.id,
            )
    else:  # subscriber
        subscriber = invoice.subscriber
        if subscriber.status == 'suspended':
            subscriber.status = 'active'
            subscriber.save(update_fields=['status', 'updated_at'])
            log_system_action(
                'tenant_subscriber.auto_reactivated', entity_type='tenant_subscriber', entity_id=subscriber.id,
                metadata={'reason': 'subscriber_invoice_paid', 'invoice_id': invoice.id}, tenant_id=subscriber.tenant_id,
            )
