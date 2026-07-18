# Dijalankan di Mikrotik TENANT (bukan di CHR) untuk konek ke VPN hub
# billinge di 103.139.163.150 lewat L2TP/IPsec. Butuh PSK tambahan dari
# admin (beda dari username/password) -- lihat docs/mikrotik-vpn-hub.md.
#
# Cara pakai:
# 1. Edit 3 variabel di bawah (username/password/PSK dari admin).
# 2. Jalankan: /import file=tenant_client_l2tp.rsc

:local vpnUsername "GANTI-USERNAME-DARI-ADMIN"
:local vpnPassword "GANTI-PASSWORD-DARI-ADMIN"
:local ipsecPsk "GANTI-PSK-DARI-ADMIN"

/interface l2tp-client add name=vpn-to-billinge connect-to=103.139.163.150 \
    user=$vpnUsername password=$vpnPassword \
    use-ipsec=yes ipsec-secret=$ipsecPsk add-default-route=no

/ip route add dst-address=192.168.38.0/24 gateway=vpn-to-billinge comment="billinge: ke LAN RADIUS lewat VPN"

:put "Selesai. Cek: /interface l2tp-client print -- status harus 'connected' dalam beberapa detik."
:put "Lanjut: /radius add service=ppp address=192.168.38.2 secret=<nas-secret-dari-dashboard> authentication-port=1812 accounting-port=1813"
:put "Lalu: /ppp aaa set use-radius=yes accounting=yes interim-update=5m"
