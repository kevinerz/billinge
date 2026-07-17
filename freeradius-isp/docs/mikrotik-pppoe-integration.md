# Mikrotik PPPoE Integration

## 1. Onboard the tenant's NAS

```sh
scripts/add_tenant.sh isp-maju "ISP Maju Jaya"          # if not already created
scripts/add_nas.sh isp-maju 203.0.113.10 maju-mikrotik-1 "Kantor pusat"
scripts/reload_freeradius.sh
```

`add_nas.sh` prints a generated shared secret — copy it, it is not
recoverable from the database afterwards (only the hash-equivalent... in
this schema it's actually stored in plaintext in `nas.secret`, which
FreeRADIUS requires; treat DB access accordingly).

`203.0.113.10` must be the IP address the RADIUS server will actually see
packets arrive from. If the Mikrotik is behind NAT/CGNAT with no stable
public IP, put it behind a VPN hub first (see
[architecture.md](architecture.md#the-fix-nas-ip--tenant_id)) and use the
VPN-assigned IP instead.

## 2. Configure the Mikrotik (RouterOS)

```
/radius add service=ppp address=<RADIUS_SERVER_IP> secret=<secret-from-step-1> \
    authentication-port=1812 accounting-port=1813

/ppp aaa set use-radius=yes accounting=yes interim-update=5m

/interface pppoe-server server add service-name=isp-maju interface=<wan-interface> \
    disabled=no
```

`interim-update=5m` makes Mikrotik send periodic accounting updates so
`radacct.acctsessiontime`/octet counters stay current for long-lived
sessions rather than only updating on session stop.

## 3. Create a subscriber

```sql
INSERT INTO radcheck (tenant_id, username, attribute, op, value)
  VALUES ((SELECT id FROM tenants WHERE slug='isp-maju'), 'budi123', 'Cleartext-Password', ':=', 'secretpass');

INSERT INTO radreply (tenant_id, username, attribute, op, value)
  VALUES ((SELECT id FROM tenants WHERE slug='isp-maju'), 'budi123', 'Mikrotik-Rate-Limit', ':=', '5M/5M');
```

`Cleartext-Password` (not a hash) is required here because Mikrotik PPP
commonly negotiates MS-CHAPv2, which needs the server to have the plaintext
password available to compute the challenge response — this is standard
practice for FreeRADIUS+Mikrotik, not a shortcut.

## 4. Test

From the Mikrotik itself: `/ppp secret` is NOT used when `use-radius=yes` —
subscribers must exist only in RADIUS, not in local PPP secrets, or the
Mikrotik will authenticate locally first and never ask RADIUS.

From the RADIUS server, using `radtest` from a host whose IP is NOT the
onboarded NAS IP will be rejected with "Unrecognized NAS" by design — that's
the tenant-resolution policy working correctly (see
[architecture.md](architecture.md)).
