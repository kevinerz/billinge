# Run once per tenant onboarding, on the CHR, AFTER setup_vpn_server.rsc.
# Creates one PPP secret usable across all three VPN protocols (OpenVPN,
# L2TP/IPsec, SSTP all authenticate against the same /ppp secret table)
# with a FIXED remote-address -- this is the IP the tenant's Mikrotik will
# always get, and the IP that must be registered as `nasname` when adding
# this tenant's NAS via the dashboard/API (see docs/mikrotik-vpn-hub.md).
#
# EDIT THESE FOUR PER TENANT, then run:
:local tenantSlug "isp-maju"
:local vpnUsername "isp-maju"
:local vpnPassword "GANTI-PASSWORD-KUAT-PER-TENANT"
:local vpnIp "10.201.0.10"

/ppp secret add name=$vpnUsername password=$vpnPassword service=any \
    profile=billinge-vpn remote-address=$vpnIp comment=("billinge tenant: " . $tenantSlug)

:put ("Tenant VPN IP (daftarkan sebagai nasname lewat dashboard/API): " . $vpnIp)
:put ("Username/password VPN buat dikirim ke tenant: " . $vpnUsername . " / " . $vpnPassword)
:put "Lanjut di dashboard: POST /api/nas/ dengan nasname = IP di atas, tenant = tenant ini"
