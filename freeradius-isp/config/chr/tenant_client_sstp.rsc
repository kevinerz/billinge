# Dijalankan di Mikrotik TENANT (bukan di CHR) untuk konek ke VPN hub
# billinge di 103.139.163.150 lewat SSTP (dipakai kalau firewall tenant
# memblokir OpenVPN -- SSTP lewat port 443, kelihatan seperti HTTPS biasa).
#
# Cara pakai:
# 1. Upload billinge-ca.crt (dari admin) ke Files Mikrotik tenant ini dulu
#    (Winbox -> Files -> drag & drop), harus sudah ada SEBELUM script ini jalan.
# 2. Edit 2 variabel di bawah (username/password dari admin).
# 3. Jalankan: /import file=tenant_client_sstp.rsc

:local vpnUsername "GANTI-USERNAME-DARI-ADMIN"
:local vpnPassword "GANTI-PASSWORD-DARI-ADMIN"

/certificate import file-name=billinge-ca.crt passphrase=""

/interface sstp-client add name=vpn-to-billinge connect-to=103.139.163.150 \
    user=$vpnUsername password=$vpnPassword \
    verify-server-certificate=yes add-default-route=no

/ip route add dst-address=192.168.38.0/24 gateway=vpn-to-billinge comment="billinge: ke LAN RADIUS lewat VPN"

:put "Selesai. Cek: /interface sstp-client print -- status harus 'connected' dalam beberapa detik."
:put "Lanjut: /radius add service=ppp address=192.168.38.2 secret=<nas-secret-dari-dashboard> authentication-port=1812 accounting-port=1813"
:put "Lalu: /ppp aaa set use-radius=yes accounting=yes interim-update=5m"
