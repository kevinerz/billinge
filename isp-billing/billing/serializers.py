from rest_framework import serializers

from .models import (
    PlatformPlan, TenantSubscription, PlatformInvoice, PlatformInvoiceItem, PlatformPayment,
    ServicePlan, SubscriberSubscription, SubscriberInvoice, SubscriberPayment,
)


# --- Platform -> Tenant ---

class PlatformPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformPlan
        fields = ['id', 'slug', 'name', 'price', 'currency', 'billing_cycle',
                  'max_subscribers', 'max_nas', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantSubscriptionSerializer(serializers.ModelSerializer):
    platform_plan_name = serializers.CharField(source='platform_plan.name', read_only=True)

    class Meta:
        model = TenantSubscription
        fields = ['id', 'tenant', 'platform_plan', 'platform_plan_name', 'status',
                  'current_period_start', 'current_period_end', 'gateway',
                  'gateway_subscription_id', 'canceled_at', 'cancellation_reason',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlatformInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformInvoiceItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'amount']
        read_only_fields = ['id']


class PlatformInvoiceSerializer(serializers.ModelSerializer):
    items = PlatformInvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = PlatformInvoice
        fields = ['id', 'tenant', 'subscription', 'billing_name', 'billing_tax_id',
                  'billing_address', 'invoice_number', 'currency', 'subtotal', 'tax_amount',
                  'total_amount', 'status', 'period_start', 'period_end', 'due_date',
                  'paid_at', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PlatformPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformPayment
        fields = ['id', 'invoice', 'tenant', 'gateway', 'gateway_order_id',
                  'gateway_transaction_id', 'payment_method', 'payment_url', 'amount',
                  'gateway_fee', 'currency', 'status', 'paid_at', 'created_at', 'updated_at']
        read_only_fields = fields  # dibuat/di-update lewat webhook gateway, bukan lewat API manual


# --- Tenant -> Pelanggannya ---

class ServicePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePlan
        fields = ['id', 'tenant', 'name', 'price', 'mikrotik_rate_limit',
                  'radius_groupname', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubscriberSubscriptionSerializer(serializers.ModelSerializer):
    service_plan_name = serializers.CharField(source='service_plan.name', read_only=True)

    class Meta:
        model = SubscriberSubscription
        fields = ['id', 'tenant', 'subscriber', 'service_plan', 'service_plan_name', 'status',
                  'current_period_start', 'current_period_end', 'gateway',
                  'gateway_subscription_id', 'canceled_at', 'cancellation_reason',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubscriberInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberInvoice
        fields = ['id', 'tenant', 'subscriber', 'subscription', 'billing_name',
                  'billing_address', 'invoice_number', 'currency', 'subtotal', 'tax_amount',
                  'total_amount', 'status', 'period_start', 'period_end', 'due_date',
                  'paid_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SubscriberPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberPayment
        fields = ['id', 'invoice', 'tenant', 'gateway', 'gateway_order_id',
                  'gateway_transaction_id', 'payment_method', 'payment_url', 'amount',
                  'gateway_fee', 'currency', 'status', 'paid_at', 'created_at', 'updated_at']
        read_only_fields = fields
