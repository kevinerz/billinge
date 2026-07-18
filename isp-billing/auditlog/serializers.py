from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'tenant_id', 'user_id', 'action', 'entity_type', 'entity_id', 'metadata', 'created_at']
        read_only_fields = fields
