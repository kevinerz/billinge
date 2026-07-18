from rest_framework import serializers

from .models import Tenant, TenantBillingProfile


class TenantBillingProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantBillingProfile
        fields = ['legal_name', 'tax_id', 'billing_email', 'billing_phone', 'billing_address', 'pic_name']


class TenantSerializer(serializers.ModelSerializer):
    billing_profile = TenantBillingProfileSerializer(read_only=True)

    class Meta:
        model = Tenant
        fields = ['id', 'slug', 'name', 'status', 'created_at', 'updated_at', 'billing_profile']
        read_only_fields = ['id', 'created_at', 'updated_at']
