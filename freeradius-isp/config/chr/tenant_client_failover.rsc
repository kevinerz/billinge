# Dijalankan di Mikrotik TENANT (bukan di CHR) -- versi GABUNGAN: bikin
# ketiga tunnel (OpenVPN, SSTP, L2TP/IPsec) sekaligus dengan kredensial
# yang sama, lalu pakai route distance supaya otomatis failover kalau
# tunnel utama putus, dan otomatis pulih lagi begitu tunnel utama nyambung
# kembali -- tidak perlu script monitoring tambahan, RouterOS yang
# menangani ini sendiri lewat status interface + jarak rute.
#
# Cara pakai:
# 1. Upload billinge-ca.crt (dari admin) ke Files Mikrotik tenant ini dulu.
# 2. Edit 3 variabel di bawah (dari dashboard, atau dari admin billinge).
# 3. Jalankan: /import file=tenant_client_failover.rsc

:local vpnUsername "GANTI-USERNAME-DARI-ADMIN"
:local vpnPassword "GANTI-PASSWORD-DARI-ADMIN"
:local ipsecPsk "GANTI-PSK-DARI-ADMIN"

/certificate import file-name=billinge-ca.crt passphrase=""

/interface ovpn-client add name=vpn-billinge-ovpn connect-to=103.139.163.150 port=1194 \
    protocol=udp user=$vpnUsername password=$vpnPassword \
    cipher=aes256-cbc auth=sha256 verify-server-certificate=yes add-default-route=no

/interface sstp-client add name=vpn-billinge-sstp connect-to=103.139.163.150 \
    user=$vpnUsername password=$vpnPassword \
    verify-server-certificate=yes add-default-route=no

/interface l2tp-client add name=vpn-billinge-l2tp connect-to=103.139.163.150 \
    user=$vpnUsername password=$vpnPassword \
    use-ipsec=yes ipsec-secret=$ipsecPsk add-default-route=no

# Failover lewat distance rute: OpenVPN diprioritaskan (distance=1), SSTP
# jadi cadangan pertama (distance=2), L2TP cadangan terakhir (distance=3).
# RouterOS otomatis pakai rute distance terkecil yang gateway-nya (tunnel
# interface-nya) sedang aktif -- begitu tunnel primer putus, rute-nya ikut
# jadi tidak aktif, lalu otomatis pindah ke distance berikutnya. Ketiga
# tunnel tetap mencoba konek terus-menerus di latar belakang (perilaku
# bawaan *-client Mikrotik), jadi begitu tunnel primer pulih, rute
# distance=1 aktif lagi otomatis -- failback otomatis juga, tanpa script
# tambahan.
/ip route add dst-address=192.168.38.0/24 gateway=vpn-billinge-ovpn distance=1 comment="billinge: primer (OpenVPN)"
/ip route add dst-address=192.168.38.0/24 gateway=vpn-billinge-sstp distance=2 comment="billinge: cadangan 1 (SSTP)"
/ip route add dst-address=192.168.38.0/24 gateway=vpn-billinge-l2tp distance=3 comment="billinge: cadangan 2 (L2TP)"

:put "Selesai. 3 tunnel dibuat, failover otomatis lewat route distance."
:put "Cek status: /interface ovpn-client print; /interface sstp-client print; /interface l2tp-client print"
:put "Cek rute aktif: /ip route print where dst-address=192.168.38.0/24 -- yang 'A' (active) itu yang lagi dipakai"
:put "Lanjut: /radius add service=ppp address=192.168.38.2 secret=<nas-secret-dari-dashboard> authentication-port=1812 accounting-port=1813"
:put "Lalu: /ppp aaa set use-radius=yes accounting=yes interim-update=5m"
