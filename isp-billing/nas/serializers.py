from django.conf import settings
from rest_framework import serializers

from .models import Nas


def render_tenant_vpn_script(nas, vpn):
    """Script RouterOS yang di-copas tenant ke Mikrotik MEREKA — 3 tunnel
    (OpenVPN/SSTP/L2TP) sekaligus dengan failover otomatis lewat route
    distance, plus langkah /radius + /ppp aaa. Semua nilai (username,
    password, IPsec PSK, RADIUS secret) sudah terisi. IPsec PSK diambil
    dari settings (.env), jadi tidak pernah dikirim mentah ke frontend —
    cuma muncul di dalam teks script ini, yang memang harus diberikan ke
    tenant."""
    host = settings.VPN_HUB_PUBLIC_HOST
    lan = settings.VPN_RADIUS_LAN
    radius_ip = settings.VPN_RADIUS_SERVER_IP
    psk = settings.VPN_IPSEC_PSK
    u = vpn.vpn_username
    p = vpn.vpn_password
    sec = nas.secret
    return f"""# Jalankan di Mikrotik TENANT. Upload dulu billinge-ca.crt (dari admin)
# ke Files. Bikin 3 tunnel sekaligus dengan failover otomatis.
:local vpnUsername "{u}"
:local vpnPassword "{p}"
:local ipsecPsk "{psk}"

/certificate import file-name=billinge-ca.crt passphrase=""

/interface ovpn-client add name=vpn-billinge-ovpn connect-to={host} port=1194 \\
    protocol=udp user=$vpnUsername password=$vpnPassword \\
    cipher=aes256-cbc auth=sha256 verify-server-certificate=yes add-default-route=no

/interface sstp-client add name=vpn-billinge-sstp connect-to={host} \\
    user=$vpnUsername password=$vpnPassword \\
    verify-server-certificate=yes add-default-route=no

/interface l2tp-client add name=vpn-billinge-l2tp connect-to={host} \\
    user=$vpnUsername password=$vpnPassword \\
    use-ipsec=yes ipsec-secret=$ipsecPsk add-default-route=no

/ip route add dst-address={lan} gateway=vpn-billinge-ovpn distance=1 comment="billinge: primer (OpenVPN)"
/ip route add dst-address={lan} gateway=vpn-billinge-sstp distance=2 comment="billinge: cadangan 1 (SSTP)"
/ip route add dst-address={lan} gateway=vpn-billinge-l2tp distance=3 comment="billinge: cadangan 2 (L2TP)"

/radius add service=ppp address={radius_ip} secret="{sec}" authentication-port=1812 accounting-port=1813
/ppp aaa set use-radius=yes accounting=yes interim-update=5m

:put "Selesai. Cek: /interface ovpn-client print; /interface sstp-client print; /interface l2tp-client print"
:put "Cek rute aktif: /ip route print where dst-address={lan}"
"""


class NasSerializer(serializers.ModelSerializer):
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    # Cuma dipakai saat create: kalau true, backend auto-daftar PPP secret+IP
    # ke CHR lewat RouterOS API. Tidak disimpan sebagai kolom nas.
    via_vpn = serializers.BooleanField(write_only=True, required=False, default=False)
    vpn_username = serializers.CharField(source='vpn.vpn_username', read_only=True, default=None)
    vpn_client_script = serializers.SerializerMethodField()

    class Meta:
        model = Nas
        fields = [
            'id', 'tenant', 'tenant_slug', 'nasname', 'shortname', 'type', 'ports',
            'secret', 'server', 'community', 'description', 'last_contact_at',
            'via_vpn', 'vpn_username', 'vpn_client_script',
        ]
        # secret SELALU digenerate otomatis di server (lihat views.py perform_create) —
        # tidak pernah diterima dari input client, biar tidak ada yang iseng pasang
        # secret lemah/dipakai ulang. last_contact_at diupdate FreeRADIUS sendiri.
        read_only_fields = ['id', 'secret', 'last_contact_at', 'vpn_username', 'vpn_client_script']

    def get_vpn_client_script(self, obj):
        vpn = getattr(obj, 'vpn', None)
        if not vpn:
            return None
        return render_tenant_vpn_script(obj, vpn)
