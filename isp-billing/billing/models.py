from django.db import models

from tenants.models import Tenant
from subscribers.models import TenantSubscriber

SUBSCRIPTION_STATUS_CHOICES = [
    ('trialing', 'Trialing'),
    ('active', 'Active'),
    ('past_due', 'Past due'),
    ('canceled', 'Canceled'),
]
INVOICE_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('pending', 'Pending'),
    ('paid', 'Paid'),
    ('overdue', 'Overdue'),
    ('void', 'Void'),
]
PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('settlement', 'Settlement'),
    ('expired', 'Expired'),
    ('failed', 'Failed'),
    ('refunded', 'Refunded'),
    ('chargeback', 'Chargeback'),
]


# ---------------------------------------------------------------------------
# Platform -> Tenant (kamu nagih ISP yang sewa platform)
# ---------------------------------------------------------------------------

class PlatformPlan(models.Model):
    id = models.BigAutoField(primary_key=True)
    slug = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='IDR')
    billing_cycle = models.CharField(max_length=10, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly')
    max_subscribers = models.PositiveIntegerField(null=True, blank=True)
    max_nas = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_plans'
        managed = False

    def __str__(self):
        return self.name


class TenantSubscription(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='subscriptions')
    platform_plan = models.ForeignKey(PlatformPlan, db_column='platform_plan_id', on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=SUBSCRIPTION_STATUS_CHOICES, default='trialing')
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    gateway = models.CharField(max_length=32, null=True, blank=True)
    gateway_subscription_id = models.CharField(max_length=128, null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenant_subscriptions'
        managed = False

    def __str__(self):
        return f'{self.tenant.slug} -> {self.platform_plan.name}'


class PlatformInvoice(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='platform_invoices')
    subscription = models.ForeignKey(TenantSubscription, db_column='subscription_id', on_delete=models.SET_NULL, null=True, blank=True)
    billing_name = models.CharField(max_length=255, null=True, blank=True)
    billing_tax_id = models.CharField(max_length=32, null=True, blank=True)
    billing_address = models.CharField(max_length=500, null=True, blank=True)
    invoice_number = models.CharField(max_length=32, unique=True)
    currency = models.CharField(max_length=3, default='IDR')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=10, choices=INVOICE_STATUS_CHOICES, default='draft')
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_invoices'
        managed = False

    def __str__(self):
        return self.invoice_number


class PlatformInvoiceItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(PlatformInvoice, db_column='invoice_id', on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = 'platform_invoice_items'
        managed = False


class PlatformPayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(PlatformInvoice, db_column='invoice_id', on_delete=models.CASCADE, related_name='payments')
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='platform_payments')
    gateway = models.CharField(max_length=32)
    gateway_order_id = models.CharField(max_length=128, null=True, blank=True)
    gateway_transaction_id = models.CharField(max_length=128, null=True, blank=True)
    payment_method = models.CharField(max_length=32, null=True, blank=True)
    payment_url = models.CharField(max_length=512, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    gateway_fee = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='IDR')
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    raw_payload = models.JSONField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'platform_payments'
        managed = False


# ---------------------------------------------------------------------------
# Tenant -> Pelanggannya (ISP nagih pelanggan sendiri)
# ---------------------------------------------------------------------------

class ServicePlan(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='service_plans')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mikrotik_rate_limit = models.CharField(max_length=64, null=True, blank=True)
    radius_groupname = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_plans'
        managed = False

    def __str__(self):
        return f'{self.name} ({self.tenant.slug})'


class SubscriberSubscription(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='subscriber_subscriptions')
    subscriber = models.ForeignKey(TenantSubscriber, db_column='subscriber_id', on_delete=models.CASCADE, related_name='subscriptions')
    service_plan = models.ForeignKey(ServicePlan, db_column='service_plan_id', on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=SUBSCRIPTION_STATUS_CHOICES, default='trialing')
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    gateway = models.CharField(max_length=32, null=True, blank=True)
    gateway_subscription_id = models.CharField(max_length=128, null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriber_subscriptions'
        managed = False


class SubscriberInvoice(models.Model):
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='subscriber_invoices')
    subscriber = models.ForeignKey(TenantSubscriber, db_column='subscriber_id', on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(SubscriberSubscription, db_column='subscription_id', on_delete=models.SET_NULL, null=True, blank=True)
    billing_name = models.CharField(max_length=255, null=True, blank=True)
    billing_address = models.CharField(max_length=500, null=True, blank=True)
    invoice_number = models.CharField(max_length=32)
    currency = models.CharField(max_length=3, default='IDR')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=10, choices=INVOICE_STATUS_CHOICES, default='draft')
    period_start = models.DateField()
    period_end = models.DateField()
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriber_invoices'
        managed = False
        unique_together = [('tenant', 'invoice_number')]

    def __str__(self):
        return self.invoice_number


class SubscriberPayment(models.Model):
    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(SubscriberInvoice, db_column='invoice_id', on_delete=models.CASCADE, related_name='payments')
    tenant = models.ForeignKey(Tenant, db_column='tenant_id', on_delete=models.CASCADE, related_name='subscriber_payments')
    gateway = models.CharField(max_length=32, null=True, blank=True)
    gateway_order_id = models.CharField(max_length=128, null=True, blank=True)
    gateway_transaction_id = models.CharField(max_length=128, null=True, blank=True)
    payment_method = models.CharField(max_length=32, null=True, blank=True)
    payment_url = models.CharField(max_length=512, null=True, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    gateway_fee = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='IDR')
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    raw_payload = models.JSONField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriber_payments'
        managed = False
