from rest_framework import serializers

from tenants.models import Tenant

from .models import VoucherBatch, Voucher


class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ['id', 'batch', 'tenant', 'username', 'status', 'redeemed_at', 'created_at']
        read_only_fields = fields  # voucher individual dibuat lewat VoucherBatch, bukan langsung


class VoucherBatchSerializer(serializers.ModelSerializer):
    # required=False: tenant_admin tidak perlu (dan tidak boleh) kirim ini —
    # view yang paksa ke tenant_id sendiri. super_admin wajib mengisinya
    # (dicek manual di views.py, bukan lewat required=True, karena kalau
    # required=True tenant_admin akan gagal validasi duluan sebelum
    # perform_create sempat menyuntikkan tenant_id-nya).
    tenant = serializers.PrimaryKeyRelatedField(queryset=Tenant.objects.all(), required=False)
    generated_by_user_email = serializers.CharField(source='generated_by_user.email', read_only=True)
    vouchers = VoucherSerializer(many=True, read_only=True)

    class Meta:
        model = VoucherBatch
        fields = [
            'id', 'tenant', 'service_plan', 'batch_code', 'quantity', 'price_each',
            'generated_by_user', 'generated_by_user_email', 'created_at', 'vouchers',
        ]
        read_only_fields = ['id', 'generated_by_user', 'created_at']
