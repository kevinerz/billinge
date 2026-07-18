# One-time setup: turns this CHR (the gateway/NAT router at 103.139.163.150,
# in front of the FreeRADIUS/Webserver/MySQL VMs on 192.168.38.0/24) into a
# VPN hub tenant Mikrotiks dial into, per docs/mikrotik-vpn-hub.md.
#
# Run once via Winbox terminal or `/import file=setup_vpn_server.rsc` after
# uploading this file to the CHR's file list.
#
# EDIT THESE FIRST:
:local wanInterface "ether1"
:local caPassphrase "GANTI-INI-PASSWORD-CA"
:local ipsecPsk "GANTI-INI-PSK-L2TP"

# --- Certificates (OpenVPN + SSTP both need the CHR to present a server
# cert; L2TP uses a pre-shared key instead, simpler and standard practice
# for a hub with an unknown/variable number of tenant peers) ---
/certificate
add name=billinge-ca-tpl common-name="Billinge VPN CA" key-usage=key-cert-sign,crl-sign days-valid=3650
sign billinge-ca-tpl name="Billinge VPN CA" ca-crl-host=103.139.163.150 passphrase=$caPassphrase
set "Billinge VPN CA" trusted=yes

add name=billinge-server-tpl common-name=103.139.163.150 key-usage=tls-server days-valid=3650
sign billinge-server-tpl ca="Billinge VPN CA" name=billinge-vpn-server passphrase=$caPassphrase
set billinge-vpn-server trusted=yes

# --- Shared PPP profile + IP pool for all three VPN types ---
# 10.201.0.1 is the CHR's own tunnel-side address; tenants get individual
# static addresses from add_tenant_vpn_client.rsc (NOT drawn from this pool
# -- the pool only exists as a fallback for any secret that omits
# remote-address). This keeps every tenant's VPN IP stable across
# reconnects, matching how nas.nasname is expected to stay stable.
/ip pool
add name=billinge-vpn-pool ranges=10.201.0.100-10.201.0.254

/ppp profile
add name=billinge-vpn local-address=10.201.0.1 remote-address=billinge-vpn-pool dns-server=1.1.1.1,1.0.0.1 use-encryption=yes

# --- OpenVPN server ---
# require-client-certificate=no: auth is username/password (the PPP
# secret from add_tenant_vpn_client.rsc), same credential works across
# all three protocols. The server cert alone still encrypts the tunnel.
# Switch to per-tenant client certificates later if a stronger posture
# is needed -- deliberately not doing that from day one, it multiplies
# onboarding work per tenant for a security gain most tenants won't need.
/interface ovpn-server server
set enabled=yes port=1194 protocol=udp mode=ip certificate=billinge-vpn-server \
    require-client-certificate=no auth=sha256 cipher=aes256-cbc \
    default-profile=billinge-vpn

# --- L2TP server + IPsec (shared PSK across all tenants -- standard
# practice for a hub with a variable/growing set of peers whose source
# IPs aren't known in advance; per-user PPP auth is still required on
# top of the PSK, so a leaked PSK alone doesn't grant tenant access) ---
/interface l2tp-server server
set enabled=yes default-profile=billinge-vpn use-ipsec=yes ipsec-secret=$ipsecPsk authentication=mschap2

# --- SSTP server (TLS on 443 -- looks like ordinary HTTPS traffic to a
# tenant's firewall, useful when OpenVPN's UDP port gets blocked) ---
/interface sstp-server server
set enabled=yes port=443 certificate=billinge-vpn-server authentication=mschap2 default-profile=billinge-vpn

# --- Firewall: allow the three VPN protocols in on the WAN interface ---
/ip firewall filter
add chain=input protocol=udp dst-port=1194 in-interface=$wanInterface action=accept comment="billinge: OpenVPN"
add chain=input protocol=tcp dst-port=443 in-interface=$wanInterface action=accept comment="billinge: SSTP"
add chain=input protocol=udp dst-port=500,4500 in-interface=$wanInterface action=accept comment="billinge: IPsec IKE/NAT-T"
add chain=input protocol=ipsec-esp in-interface=$wanInterface action=accept comment="billinge: IPsec ESP"

# --- THE IMPORTANT PART: tenant VPN traffic reaching the internal LAN
# must be ROUTED, not masqueraded/NAT'd. If it gets NAT'd to the CHR's own
# LAN-side address before reaching FreeRADIUS, every tenant's Mikrotik
# would appear to RADIUS as the SAME source IP (the CHR), collapsing the
# whole NAS-IP-based tenant-resolution model this project depends on
# (see architecture.md). place-before=0 makes this the FIRST NAT rule
# checked, so it wins over any general masquerade rule already in place. ---
/ip firewall nat
add chain=srcnat src-address=10.201.0.0/24 dst-address=192.168.38.0/24 action=accept \
    place-before=0 comment="billinge: never NAT tenant VPN traffic reaching the LAN"

:put "Done. Next: run add_tenant_vpn_client.rsc once per tenant."
