# Mikrotik VPN Hub (for tenants behind NAT/CGNAT)

## Why this exists

The tenant-resolution model this whole project depends on
([architecture.md](architecture.md#the-fix-nas-ip--tenant_id)) resolves a
tenant from the source IP of the incoming RADIUS packet. That only works if
each tenant's Mikrotik has a stable IP as seen by the FreeRADIUS server. A
tenant behind NAT/CGNAT with no fixed public IP breaks this outright —
`architecture.md` flagged this as an operational constraint from day one,
deferred until an actual tenant needed it.

The fix: tenants without a stable public IP dial into a VPN hub instead,
and get a **fixed internal IP** from the hub every time they connect. That
fixed IP is what gets registered as `nas.nasname`, exactly like a directly
reachable Mikrotik would use its real public IP.

## Architecture

The CHR (Mikrotik Cloud Hosted Router) at `103.139.163.150` is the
gateway/NAT router already sitting in front of the FreeRADIUS/Webserver/MySQL
VMs on `192.168.38.0/24` — it's the natural place to terminate tenant VPN
connections, not a separate box, since it already routes to that LAN.

- Tenants dial in via **OpenVPN**, **L2TP/IPsec**, or **SSTP** (pick
  whichever the tenant's own firewall allows through — see "Choosing a
  protocol" below). PPTP is deliberately not offered — its crypto
  (MPPE/MS-CHAPv2) has been considered broken for years.
- All three protocols share **one PPP secret per tenant** (`service=any`)
  and **one PPP profile**, so switching a tenant from one protocol to
  another later doesn't need new credentials.
- Each tenant gets a **fixed `remote-address`** (from `10.201.0.0/24`,
  distinct from the LAN `192.168.38.0/24` and the local dev-test range
  `10.99.0.0/24`) set directly on their PPP secret — not drawn from the
  pool — so the IP never changes across reconnects.
- **Critical:** traffic from `10.201.0.0/24` reaching `192.168.38.0/24` is
  explicitly excluded from NAT/masquerade on the CHR (see the `place-before=0`
  NAT rule in `setup_vpn_server.rsc`). If it were masqueraded, every tenant's
  traffic would arrive at FreeRADIUS looking like it came from the CHR
  itself — collapsing tenant resolution back to the exact global-username
  collision problem this project was built to solve. This is routed, not
  NAT'd, on purpose.

## One-time CHR setup

Upload `config/chr/setup_vpn_server.rsc` to the CHR's file list (Winbox →
Files → drag and drop) and run it:

```
/import file=setup_vpn_server.rsc
```

Edit the three variables at the top of that script first (WAN interface
name, a CA passphrase, an IPsec PSK) — see the comments in the file for
what each protects.

This creates: the CA + server certificate (for OpenVPN/SSTP), the shared
PPP profile and IP pool, all three VPN servers, the firewall rules to
allow them in, and the NAT exception described above. Run once, ever —
not per tenant.

After it runs, export the CA certificate's public half for distribution
to tenants (they need it to verify the server during OpenVPN/SSTP
handshake):

```
/certificate export-certificate "Billinge VPN CA" type=pem
```

This drops a `.crt` file in the CHR's file list — download it and send it
to each tenant alongside their credentials.

## Onboarding a tenant

1. Run `config/chr/add_tenant_vpn_client.rsc` on the CHR, editing the four
   variables at the top (tenant slug, VPN username/password, the fixed
   `10.201.0.x` address to assign — pick the next unused one).
2. Send the tenant: their VPN username/password, the CA cert file, and
   whichever client config below matches the protocol they'll use.
3. Register the NAS via the dashboard/API once the tenant confirms their
   Mikrotik is connected: `POST /api/nas/` with `nasname` set to the
   `10.201.0.x` address from step 1 — same as any other NAS, the fact that
   it arrives over a VPN tunnel is invisible to FreeRADIUS from here on.

## Tenant-side Mikrotik client config

Give the tenant whichever one of these three matches their situation —
all three authenticate against the same PPP secret from step 1 above.
`add-default-route=no` on every variant is deliberate: this tunnel exists
to reach the RADIUS server, not to become the tenant's general internet
uplink.

### OpenVPN (recommended default — simplest, most standard)

```
/certificate import file-name=billinge-ca.crt passphrase=""

/interface ovpn-client add name=vpn-to-billinge connect-to=103.139.163.150 port=1194 \
    protocol=udp user=<vpn-username> password=<vpn-password> \
    cipher=aes256-cbc auth=sha256 verify-server-certificate=yes add-default-route=no

/ip route add dst-address=192.168.38.0/24 gateway=vpn-to-billinge
```

### SSTP (if the tenant's firewall blocks OpenVPN's UDP port — SSTP rides
TLS on port 443 and looks like ordinary HTTPS)

```
/certificate import file-name=billinge-ca.crt passphrase=""

/interface sstp-client add name=vpn-to-billinge connect-to=103.139.163.150 \
    user=<vpn-username> password=<vpn-password> \
    verify-server-certificate=yes add-default-route=no

/ip route add dst-address=192.168.38.0/24 gateway=vpn-to-billinge
```

### L2TP/IPsec (third option — needs the shared IPsec PSK from the admin
in addition to the PPP username/password)

```
/interface l2tp-client add name=vpn-to-billinge connect-to=103.139.163.150 \
    user=<vpn-username> password=<vpn-password> \
    use-ipsec=yes ipsec-secret=<ipsec-psk-from-admin> add-default-route=no

/ip route add dst-address=192.168.38.0/24 gateway=vpn-to-billinge
```

### Then, same as any directly-reachable Mikrotik

```
/radius add service=ppp address=192.168.38.2 secret=<nas-secret-from-dashboard> \
    authentication-port=1812 accounting-port=1813
/ppp aaa set use-radius=yes accounting=yes interim-update=5m
```

(`192.168.38.2` is the FreeRADIUS VM's real LAN address — reachable now
because of the route added above, not because it's been given any special
public-facing address.)

## Choosing a protocol

Default new tenants to **OpenVPN** — least overhead, most standard, works
almost everywhere. Fall back to **SSTP** specifically when a tenant reports
their firewall blocks it (SSTP's port-443-over-TLS is much harder for a
corporate firewall to distinguish from normal browsing traffic). Offer
**L2TP/IPsec** as a third option mainly for older Mikrotik hardware or
tenants who already run L2TP/IPsec elsewhere and want one less thing to
learn — it needs one more shared secret (the IPsec PSK) than the other two.

## Revoking a tenant

```
/ppp secret remove [find comment~"billinge tenant: isp-maju"]
/ppp active remove [find name=<vpn-username>]
```

Removing the secret prevents future reconnects; removing the active
session (if connected right now) disconnects it immediately. Also disable
or delete the tenant's NAS entry via the dashboard/API — leaving it
active would just mean the next different tenant who happens to reuse that
`10.201.0.x` address inherits the old NAS registration, which is exactly
the kind of stale-NAS-IP problem `scripts/update_nas_ip.sh` already exists
to catch (see the Mikrotik offline/reconnect docs), but avoiding it in the
first place is simpler than relying on that safety net.
