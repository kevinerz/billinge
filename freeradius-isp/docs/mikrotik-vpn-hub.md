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

### Option A — from the dashboard (recommended)

The **VPN Hub** page (tenant_admin+, same tier as NAS) generates a random
password + IPsec PSK, saves them as a `TenantIntegration`
(`integration_type=vpn_hub`), and immediately renders both scripts below
with the real values already filled in and a **Copy** button on each —
nothing to hand-edit. Credentials are `write_only` on the API (same as
every other integration type and NAS's `secret`), so this is the only
time they're ever shown; the page warns about that before you navigate
away. Paste script 1 into the CHR, script 2 into the tenant's Mikrotik.

### Option B — by hand, from the .rsc files in this repo

1. Run `config/chr/add_tenant_vpn_client.rsc` on the CHR, editing the four
   variables at the top (tenant slug, VPN username/password, the fixed
   `10.201.0.x` address to assign — pick the next unused one).
2. Send the tenant a ready-to-run script — **this is the file the tenant
   actually copies onto their own Mikrotik**, not something to retype by
   hand:
   - `config/chr/tenant_client_failover.rsc` — recommended default, all
     three protocols at once with automatic failover (see below)
   - `config/chr/tenant_client_openvpn.rsc` / `_sstp.rsc` / `_l2tp.rsc` —
     single-protocol variants, if a tenant only wants one

   Each file has `GANTI-...` placeholder variables at the top for the
   tenant to fill in with the credentials from step 1, then run via
   `/import file=<the-file>.rsc` on their own router —
   Winbox → Files → upload the `.rsc` (and, for OpenVPN/SSTP, the
   `billinge-ca.crt` from the step above) → Terminal → `/import`. Each
   script prints its own next steps (checking the tunnel connected, then
   adding the `/radius` client and `/ppp aaa` settings) when it finishes.
3. Register the NAS via the dashboard/API once the tenant confirms their
   Mikrotik is connected: `POST /api/nas/` with `nasname` set to the
   `10.201.0.x` address from step 1 — same as any other NAS, the fact that
   it arrives over a VPN tunnel is invisible to FreeRADIUS from here on.

All three client scripts set `add-default-route=no` deliberately — this
tunnel exists to reach the RADIUS server, not to become the tenant's
general internet uplink — and route only `192.168.38.0/24` (the RADIUS
LAN) through the tunnel, ending with the same `/radius add
address=192.168.38.2 ...` + `/ppp aaa set use-radius=yes` steps as any
directly-reachable Mikrotik would use (`192.168.38.2` — FreeRADIUS's real
LAN address — is reachable now purely because of the route the script
added, not because it's been given any special public-facing address).

## Automatic failover (tenant_client_failover.rsc / dashboard script 2)

This variant dials all three protocols at once and adds one route to
`192.168.38.0/24` per tunnel, with increasing `distance` (OpenVPN=1,
SSTP=2, L2TP=3). RouterOS always uses the lowest-distance route whose
gateway interface is actually up — no monitoring script needed:

- Primary tunnel drops → its route becomes inactive → RouterOS
  automatically starts using the next-distance route through whichever
  backup tunnel is still connected.
- All three `*-client` interfaces keep trying to (re)connect in the
  background the whole time, regardless of which one is currently
  carrying traffic — Mikrotik's built-in behavior for these interface
  types, nothing configured here creates that retry loop.
- Once the primary tunnel reconnects, its distance-1 route becomes active
  again automatically — failback is automatic too, not just failover.

Use the single-protocol scripts instead only when a tenant specifically
wants just one tunnel (e.g. to minimize the number of open connections on
a constrained device) — otherwise the failover variant is strictly a
superset of what they do individually.

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
