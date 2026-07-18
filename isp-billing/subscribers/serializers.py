from rest_framework import serializers

from .models import TenantSubscriber


class TenantSubscriberSerializer(serializers.ModelSerializer):
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)

    class Meta:
        model = TenantSubscriber
        fields = [
            'id', 'tenant', 'tenant_slug', 'username', 'full_name', 'phone', 'email',
            'identity_type', 'identity_number', 'address', 'install_lat', 'install_lng',
            'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
