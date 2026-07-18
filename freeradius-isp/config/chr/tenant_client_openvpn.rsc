# Dijalankan di Mikrotik TENANT (bukan di CHR) untuk konek ke VPN hub
# billinge di 103.139.163.150 lewat OpenVPN. Kredensial & file CA di bawah
# dikirim oleh admin billinge setelah menjalankan add_tenant_vpn_client.rsc.
#
# Cara pakai:
# 1. Upload billinge-ca.crt (dari admin) ke Files Mikrotik tenant ini dulu
#    (Winbox -> Files -> drag & drop), harus sudah ada SEBELUM script ini jalan.
# 2. Edit 2 variabel di bawah (username/password dari admin).
# 3. Jalankan: /import file=tenant_client_openvpn.rsc

:local vpnUsername "GANTI-USERNAME-DARI-ADMIN"
:local vpnPassword "GANTI-PASSWORD-DARI-ADMIN"

/certificate import file-name=billinge-ca.crt passphrase=""

/interface ovpn-client add name=vpn-to-billinge connect-to=103.139.163.150 port=1194 \
    protocol=udp user=$vpnUsername password=$vpnPassword \
    cipher=aes256-cbc auth=sha256 verify-server-certificate=yes add-default-route=no

# Route ini yang bikin tunnel-nya berguna -- tanpa ini, Mikrotik tenant
# konek ke VPN tapi tidak tahu harus lewat situ untuk menjangkau FreeRADIUS.
# Tunggu status interface vpn-to-billinge jadi "connected" dulu (cek:
# /interface ovpn-client print) sebelum route ini benar-benar berfungsi.
/ip route add dst-address=192.168.38.0/24 gateway=vpn-to-billinge comment="billinge: ke LAN RADIUS lewat VPN"

:put "Selesai. Cek: /interface ovpn-client print -- status harus 'connected' dalam beberapa detik."
:put "Lanjut: /radius add service=ppp address=192.168.38.2 secret=<nas-secret-dari-dashboard> authentication-port=1812 accounting-port=1813"
:put "Lalu: /ppp aaa set use-radius=yes accounting=yes interim-update=5m"
