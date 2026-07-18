"""Billing engine — generate invoice periode berikutnya sebelum periode
berjalan habis, tandai invoice yang lewat jatuh tempo sebagai overdue, dan
auto-suspend tenant/subscriber yang telat bayar lebih dari masa tenggang.
Dijadwalkan harian lewat Celery beat (lihat CELERY_BEAT_SCHEDULE di
config/settings.py) via run_daily_billing_cycle di bawah.

Sisi pembayaran (invoice jadi 'paid' + reaktivasi tenant/subscriber yang
sempat disuspend) ditangani REAL-TIME oleh webhooks/views.py lewat
billing/services.py, BUKAN di sini — supaya akses tidak perlu nunggu
sampai jadwal harian berikutnya baru pulih setelah bayar.

Keterbatasan yang disengaja: service_plans (langganan tenant->subscriber)
tidak punya kolom billing_cycle sendiri di schema — diasumsikan bulanan
untuk semua service_plan. platform_plans.billing_cycle (monthly/yearly)
dipakai apa adanya untuk tenant_subscriptions. Tidak ada perhitungan pajak
otomatis (tax_amount selalu 0) karena tidak ada tarif pajak di schema mana
pun — invoice yang digenerate otomatis murni subtotal = total.
"""
import calendar
import datetime

from celery import shared_task
from django.utils import timezone

from auditlog.helpers import log_system_action
from subscribers.models import TenantSubscriber
from tenants.models import Tenant

from .models import PlatformInvoice, SubscriberInvoice, SubscriberSubscription, TenantSubscription

INVOICE_LEAD_DAYS = 3  # generate invoice periode berikutnya H-3 sebelum periode berjalan habis
GRACE_DAYS = 3  # berapa hari lewat jatuh tempo sebelum auto-suspend


def add_cycle(d, cycle):
    """Tambah satu siklus billing ke tanggal `d`. Pakai stdlib murni
    (bukan dateutil, tidak ada di requirements.txt) — cukup untuk
    monthly/yearly, clamp tanggal kalau bulan tujuan lebih pendek
    (mis. 31 Jan + 1 bulan -> 28/29 Feb, bukan meluber ke Maret)."""
    if cycle == 'monthly':
        month = d.month + 1
        year = d.year + (month - 1) // 12
        month = (month - 1) % 12 + 1
    elif cycle == 'yearly':
        month = d.month
        year = d.year + 1
    else:
        raise ValueError(f'billing_cycle tidak dikenal: {cycle}')
    last_day = calendar.monthrange(year, month)[1]
    return datetime.date(year, month, min(d.day, last_day))


@shared_task
def generate_platform_invoices():
    """platform_invoices berikutnya buat tenant_subscriptions yang aktif/trial
    dan periode berjalannya mau habis dalam INVOICE_LEAD_DAYS hari (atau
    malah sudah lewat — self-healing kalau task ini sempat tidak jalan
    beberapa hari)."""
    cutoff = timezone.localdate() + datetime.timedelta(days=INVOICE_LEAD_DAYS)
    created = 0
    subs = TenantSubscription.objects.select_related('tenant', 'platform_plan').filter(
        status__in=['trialing', 'active'], current_period_end__lte=cutoff,
    )
    for sub in subs:
        period_start = sub.current_period_end
        if PlatformInvoice.objects.filter(subscription=sub, period_start=period_start).exists():
            continue
        period_end = add_cycle(period_start, sub.platform_plan.billing_cycle)
        amount = sub.platform_plan.price
        PlatformInvoice.objects.create(
            tenant=sub.tenant, subscription=sub,
            invoice_number=f'PINV-{sub.tenant_id}-{period_start.strftime("%Y%m")}-{sub.id}',
            subtotal=amount, tax_amount=0, total_amount=amount,
            status='pending', period_start=period_start, period_end=period_end, due_date=period_start,
        )
        created += 1
    return created


@shared_task
def generate_subscriber_invoices():
    """Sama seperti generate_platform_invoices, level tenant->subscriber."""
    cutoff = timezone.localdate() + datetime.timedelta(days=INVOICE_LEAD_DAYS)
    created = 0
    subs = SubscriberSubscription.objects.select_related('tenant', 'subscriber', 'service_plan').filter(
        status__in=['trialing', 'active'], current_period_end__lte=cutoff,
    )
    for sub in subs:
        period_start = sub.current_period_end
        if SubscriberInvoice.objects.filter(subscription=sub, period_start=period_start).exists():
            continue
        period_end = add_cycle(period_start, 'monthly')
        amount = sub.service_plan.price
        SubscriberInvoice.objects.create(
            tenant=sub.tenant, subscriber=sub.subscriber, subscription=sub,
            invoice_number=f'SINV-{sub.tenant_id}-{period_start.strftime("%Y%m")}-{sub.id}',
            subtotal=amount, tax_amount=0, total_amount=amount,
            status='pending', period_start=period_start, period_end=period_end, due_date=period_start,
        )
        created += 1
    return created


@shared_task
def mark_overdue_platform_invoices():
    today = timezone.localdate()
    count = 0
    qs = PlatformInvoice.objects.select_related('subscription').filter(status='pending', due_date__lt=today)
    for inv in qs:
        inv.status = 'overdue'
        inv.save(update_fields=['status', 'updated_at'])
        if inv.subscription and inv.subscription.status == 'active':
            inv.subscription.status = 'past_due'
            inv.subscription.save(update_fields=['status', 'updated_at'])
        count += 1
    return count


@shared_task
def mark_overdue_subscriber_invoices():
    today = timezone.localdate()
    count = 0
    qs = SubscriberInvoice.objects.select_related('subscription').filter(status='pending', due_date__lt=today)
    for inv in qs:
        inv.status = 'overdue'
        inv.save(update_fields=['status', 'updated_at'])
        if inv.subscription and inv.subscription.status == 'active':
            inv.subscription.status = 'past_due'
            inv.subscription.save(update_fields=['status', 'updated_at'])
        count += 1
    return count


@shared_task
def suspend_overdue_tenants():
    """Tenant yang punya platform_invoice overdue lebih dari GRACE_DAYS hari
    -> tenants.status='suspended', yang sudah digate di RADIUS authorize
    (policy.d/isp_tenant isp_tenant_check_active) jadi langsung berlaku."""
    threshold = timezone.localdate() - datetime.timedelta(days=GRACE_DAYS)
    tenant_ids = list(
        PlatformInvoice.objects.filter(status='overdue', due_date__lt=threshold)
        .values_list('tenant_id', flat=True).distinct()
    )
    if not tenant_ids:
        return 0
    count = 0
    for tenant in Tenant.objects.filter(id__in=tenant_ids, status='active'):
        tenant.status = 'suspended'
        tenant.save(update_fields=['status', 'updated_at'])
        log_system_action('tenant.auto_suspended', entity_type='tenant', entity_id=tenant.id,
                           metadata={'reason': 'platform_invoice_overdue'}, tenant_id=tenant.id)
        count += 1
    return count


@shared_task
def suspend_overdue_subscribers():
    """Sama seperti suspend_overdue_tenants, level subscriber.
    CATATAN: tenant_subscribers.status='suspended' BELUM digate di RADIUS
    authorize (cuma tenants.status yang dicek saat ini, lihat
    policy.d/isp_tenant) — jadi baris ini update status di dashboard/DB
    tapi subscriber yang bersangkutan masih bisa login RADIUS sampai
    policy RADIUS-nya diperluas buat cek status subscriber juga. Ditandai
    sebagai gap, bukan tersembunyi."""
    threshold = timezone.localdate() - datetime.timedelta(days=GRACE_DAYS)
    subscriber_ids = list(
        SubscriberInvoice.objects.filter(status='overdue', due_date__lt=threshold)
        .values_list('subscriber_id', flat=True).distinct()
    )
    if not subscriber_ids:
        return 0
    count = 0
    for subscriber in TenantSubscriber.objects.filter(id__in=subscriber_ids, status='active'):
        subscriber.status = 'suspended'
        subscriber.save(update_fields=['status', 'updated_at'])
        log_system_action('tenant_subscriber.auto_suspended', entity_type='tenant_subscriber', entity_id=subscriber.id,
                           metadata={'reason': 'subscriber_invoice_overdue'}, tenant_id=subscriber.tenant_id)
        count += 1
    return count


@shared_task
def run_daily_billing_cycle():
    return {
        'platform_invoices_created': generate_platform_invoices(),
        'subscriber_invoices_created': generate_subscriber_invoices(),
        'platform_invoices_overdue': mark_overdue_platform_invoices(),
        'subscriber_invoices_overdue': mark_overdue_subscriber_invoices(),
        'tenants_suspended': suspend_overdue_tenants(),
        'subscribers_suspended': suspend_overdue_subscribers(),
    }
