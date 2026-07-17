# Mikrotik Hotspot Integration

## 1. Onboard the tenant's NAS

Same as [PPPoE](mikrotik-pppoe-integration.md#1-onboard-the-tenants-nas):

```sh
scripts/add_nas.sh isp-maju 203.0.113.20 maju-mikrotik-hotspot-1 "Hotspot lokasi A"
scripts/reload_freeradius.sh
```

A single Mikrotik can run both PPPoE and Hotspot — it is still one NAS
(one IP → one tenant), so one `nas` row covers both.

## 2. Configure the Mikrotik (RouterOS)

```
/radius add service=hotspot address=<RADIUS_SERVER_IP> secret=<secret-from-step-1> \
    authentication-port=1812 accounting-port=1813

/ip hotspot profile set [find] use-radius=yes accounting=yes
```

## 3. Vouchers vs named subscribers

Two common hotspot patterns, both just rows in `radcheck`/`radreply` scoped
by `tenant_id`:

- **Named subscriber** (same as PPPoE): a fixed `Cleartext-Password`.
- **Prepaid voucher**: generate a random username+password pair per
  voucher, optionally with a `Session-Timeout` or `Mikrotik-Total-Limit`
  reply attribute for time/data-capped access. Vouchers are still just
  `radcheck`/`radreply` rows with `tenant_id` set — no separate voucher
  table is needed unless you later want to track voucher batches/sale price,
  which would live in the billing seam (`sql/004_billing_seam.sql`).

```sql
INSERT INTO radcheck (tenant_id, username, attribute, op, value)
  VALUES ((SELECT id FROM tenants WHERE slug='isp-maju'), 'voucher-8f3a2c', 'Cleartext-Password', ':=', 'x7k2p9');

INSERT INTO radreply (tenant_id, username, attribute, op, value)
  VALUES ((SELECT id FROM tenants WHERE slug='isp-maju'), 'voucher-8f3a2c', 'Session-Timeout', ':=', '3600');
```

## 4. Data-cap billing note

For usage-based hotspot billing (e.g. "2GB voucher"), aggregate
`radacct.acctinputoctets + acctoutputoctets` by `(tenant_id, username)` —
`radacct` already carries `tenant_id` from `queries.conf`, so this is a
direct filtered query, no join needed. Enforcing a hard cutoff mid-session
(rather than just reporting after the fact) needs a Mikrotik-side mechanism
(e.g. `Mikrotik-Total-Limit` reply attribute, checked by RouterOS itself) —
FreeRADIUS accounting alone does not disconnect an active session.
