from rest_framework import serializers

from .models import PaymentGatewayEvent, PaymentRefund


class PaymentGatewayEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGatewayEvent
        fields = ['id', 'payment_type', 'payment_id', 'gateway', 'event_type', 'status_reported', 'payload', 'received_at']
        read_only_fields = fields


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = ['id', 'payment_type', 'payment_id', 'amount', 'reason', 'gateway_refund_id', 'status', 'created_at', 'updated_at']
        read_only_fields = fields
