from django.db import models


class PaymentGatewayEvent(models.Model):
    """Log lengkap tiap webhook masuk dari gateway — bukan cuma status
    terakhir. Gateway suka retry pengiriman webhook, dan notifikasi
    'pending' yang telat/rusak urutannya bisa datang SETELAH 'settlement' —
    riwayat penuh ini yang membuat status transition forward-only bisa
    dicek dan jadi jejak audit kalau rekonsiliasi meleset.
    payment_type/payment_id itu polimorfik (platform_payments ATAU
    subscriber_payments) — sengaja tanpa FK, sama seperti notifications."""

    PAYMENT_TYPE_CHOICES = [
        ('platform', 'Platform'),
        ('subscriber', 'Subscriber'),
    ]

    id = models.BigAutoField(primary_key=True)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    payment_id = models.BigIntegerField()
    gateway = models.CharField(max_length=32)
    event_type = models.CharField(max_length=64, null=True, blank=True)
    status_reported = models.CharField(max_length=32, null=True, blank=True)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payment_gateway_events'
        managed = False  # tabel sudah ada dari sql/013_payment_gateway_resilience.sql

    def __str__(self):
        return f'{self.gateway}:{self.payment_type}:{self.payment_id}:{self.status_reported}'


class PaymentRefund(models.Model):
    """Refund/chargeback parsial bisa terjadi lebih dari sekali per payment,
    masing-masing punya alasan & id refund sisi gateway sendiri — bukan
    boolean tunggal. Sama pola polimorfik seperti di atas."""

    PAYMENT_TYPE_CHOICES = [
        ('platform', 'Platform'),
        ('subscriber', 'Subscriber'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.BigAutoField(primary_key=True)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    payment_id = models.BigIntegerField()
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.CharField(max_length=255, null=True, blank=True)
    gateway_refund_id = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payment_refunds'
        managed = False  # tabel sudah ada dari sql/013_payment_gateway_resilience.sql

    def __str__(self):
        return f'{self.payment_type}:{self.payment_id}:{self.status}'
