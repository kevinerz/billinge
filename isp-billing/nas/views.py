import secrets as secrets_lib  # nama beda dari field model `secret`

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from auditlog.helpers import log_action
from common.permissions import IsSuperAdminOnly

from .models import Nas, NasVpnCredential
from .routeros import RouterOsError, add_vpn_secret, remove_vpn_secret
from .serializers import NasSerializer


class NasViewSet(viewsets.ModelViewSet):
    """
    Manajemen router Mikrotik + VPN. SUPER_ADMIN SAJA — ini infrastruktur
    yang DISEDIAKAN PLATFORM ke tenant (daftar NAS, setup VPN dial-in,
    alokasi IP saat onboarding). Tenant tidak mengelola sendiri. nas.secret
    itu kredensial RADIUS asli & salah konfigurasi NAS bisa memutus seluruh
    pelanggan tenant sekaligus — jadi memang domain platform, bukan tenant.
    """
    serializer_class = NasSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOnly]

    def get_queryset(self):
        return Nas.objects.select_related('tenant', 'vpn').order_by('-id')

    def perform_create(self, serializer):
        # Secret digenerate baru & acak tiap NAS, tidak pernah dari input
        # client — satu router bocor tidak akan membocorkan secret router lain.
        generated_secret = secrets_lib.token_urlsafe(24)
        # via_vpn cuma flag proses, bukan kolom nas — buang dari data sebelum save.
        via_vpn = serializer.validated_data.pop('via_vpn', False)
        user = self.request.user
        if user.role == 'super_admin':
            nas = serializer.save(secret=generated_secret)
        else:
            nas = serializer.save(tenant_id=user.tenant_id, secret=generated_secret)
        log_action(
            self.request, 'nas.created', entity_type='nas', entity_id=nas.id,
            metadata={'nasname': nas.nasname, 'shortname': nas.shortname, 'via_vpn': via_vpn},
            tenant_id=nas.tenant_id,
        )

        if via_vpn:
            self._provision_vpn(nas)

    def _provision_vpn(self, nas):
        """Daftarkan PPP secret+IP tenant ke CHR lewat RouterOS API, lalu
        simpan kredensialnya. Kalau CHR gagal dihubungi, ROLLBACK NAS-nya
        supaya tidak ada NAS setengah jadi (terdaftar di DB tapi tidak bisa
        dial-in)."""
        vpn_username = f't{nas.tenant_id}-nas{nas.id}'
        vpn_password = secrets_lib.token_urlsafe(18)
        try:
            add_vpn_secret(
                vpn_username, vpn_password, nas.nasname,
                comment=f'billinge nas {nas.id} (tenant {nas.tenant_id})',
            )
        except RouterOsError as e:
            nas.delete()  # cascade juga menghapus baris nas_vpn_credentials kalau ada
            raise ValidationError({'via_vpn': str(e)})

        NasVpnCredential.objects.create(
            nas=nas, vpn_username=vpn_username, vpn_password=vpn_password, remote_address=nas.nasname,
        )
        log_action(
            self.request, 'nas.vpn_provisioned', entity_type='nas', entity_id=nas.id,
            metadata={'vpn_username': vpn_username, 'remote_address': nas.nasname}, tenant_id=nas.tenant_id,
        )

    def perform_destroy(self, instance):
        vpn = getattr(instance, 'vpn', None)
        if vpn:
            # Best-effort: hapus PPP secret di CHR. Kalau CHR sedang tidak
            # reachable, jangan gagalkan penghapusan NAS — cukup catat.
            # Baris nas_vpn_credentials ikut terhapus otomatis (FK CASCADE).
            try:
                remove_vpn_secret(vpn.vpn_username)
            except RouterOsError as e:
                log_action(
                    self.request, 'nas.vpn_deprovision_failed', entity_type='nas', entity_id=instance.id,
                    metadata={'vpn_username': vpn.vpn_username, 'error': str(e)}, tenant_id=instance.tenant_id,
                )
        log_action(
            self.request, 'nas.deleted', entity_type='nas', entity_id=instance.id,
            metadata={'nasname': instance.nasname}, tenant_id=instance.tenant_id,
        )
        instance.delete()
