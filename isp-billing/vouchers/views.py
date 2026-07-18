from django.db import connection, transaction
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from auditlog.helpers import log_action
from common.permissions import IsSuperAdminOrTenantAdmin, scope_queryset_to_tenant

from .models import VoucherBatch, Voucher
from .radius import delete_radius_credentials, insert_radius_credential, unique_voucher_username
from .serializers import VoucherBatchSerializer, VoucherSerializer

# Batas atas jaga-jaga — generate voucher jalan sinkron dalam satu
# request/transaction, bukan lewat job queue, jadi angka yang kebablasan
# (salah ketik nol) bisa bikin request timeout / lock tabel lama.
MAX_BATCH_QUANTITY = 5000


class VoucherBatchViewSet(viewsets.ModelViewSet):
    """
    Generate & kelola batch voucher hotspot. Dibatasi tenant_admin ke atas —
    sama seperti NAS, ini membuat kredensial RADIUS asli (radcheck), bukan
    cuma data biasa.
    """
    serializer_class = VoucherBatchSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = VoucherBatch.objects.select_related('tenant', 'service_plan', 'generated_by_user') \
            .prefetch_related('vouchers').order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)

    def perform_create(self, serializer):
        request = self.request
        user = request.user
        data = serializer.validated_data
        quantity = data['quantity']
        if quantity < 1 or quantity > MAX_BATCH_QUANTITY:
            raise ValidationError({'quantity': f'Harus antara 1 dan {MAX_BATCH_QUANTITY}.'})

        if user.role == 'super_admin':
            tenant = data.get('tenant')
            if tenant is None:
                raise ValidationError({'tenant': 'Wajib diisi.'})
            tenant_id = tenant.id
        else:
            tenant_id = user.tenant_id

        service_plan = data.get('service_plan')
        if service_plan and service_plan.tenant_id != tenant_id:
            raise ValidationError({'service_plan': 'service_plan ini bukan milik tenant tersebut.'})

        if VoucherBatch.objects.filter(tenant_id=tenant_id, batch_code=data['batch_code']).exists():
            raise ValidationError({'batch_code': 'Sudah dipakai di tenant ini.'})

        with transaction.atomic():
            if user.role == 'super_admin':
                batch = serializer.save(generated_by_user=user)
            else:
                batch = serializer.save(tenant_id=tenant_id, generated_by_user=user)

            groupname = service_plan.radius_groupname if service_plan else None
            reserved = set()
            with connection.cursor() as cursor:
                for _ in range(quantity):
                    code = unique_voucher_username(tenant_id, reserved)
                    reserved.add(code)
                    insert_radius_credential(cursor, tenant_id, code, code, groupname)
                    Voucher.objects.create(batch=batch, tenant_id=tenant_id, username=code, status='unused')

        log_action(
            request, 'voucher_batch.created', entity_type='voucher_batch', entity_id=batch.id,
            metadata={'batch_code': batch.batch_code, 'quantity': quantity}, tenant_id=tenant_id,
        )

    def perform_destroy(self, instance):
        usernames = list(instance.vouchers.values_list('username', flat=True))
        tenant_id = instance.tenant_id
        # Hapus kredensial RADIUS DULU, baru batch-nya — kalau kebalik dan
        # request putus di tengah, mendingan ada batch record tanpa
        # kredensial (janggal tapi aman) daripada kredensial hidup tanpa
        # jejak batch-nya (voucher gratis yang tidak tercatat di mana pun).
        delete_radius_credentials(tenant_id, usernames)
        log_action(
            self.request, 'voucher_batch.deleted', entity_type='voucher_batch', entity_id=instance.id,
            metadata={'batch_code': instance.batch_code, 'voucher_count': len(usernames)}, tenant_id=tenant_id,
        )
        instance.delete()  # cascade DB menghapus baris `vouchers` terkait


class VoucherViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — voucher individual dibuat massal lewat VoucherBatchViewSet,
    bukan satu-satu lewat endpoint ini."""
    serializer_class = VoucherSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = Voucher.objects.select_related('tenant', 'batch').order_by('-created_at')
        return scope_queryset_to_tenant(qs, self.request.user)
