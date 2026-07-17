# Architecture

## Model

One shared FreeRADIUS 3.2 instance, one shared MySQL database, serving many
tenants (ISPs/resellers renting the platform). Isolation between tenants is
enforced at the SQL row level via a `tenant_id` column on every relevant
table — not by giving each tenant its own container/database. This fits the
target scale (tens–low hundreds of tenants, thousands of subscribers) without
the operational overhead of per-tenant infrastructure.

## Deployment

FreeRADIUS installs directly on an Ubuntu 24.04 VM — no Docker. MySQL runs
on a **separate** server, reached over the network via `MYSQL_HOST` in
`.env`, not localhost. `scripts/install_ubuntu.sh` installs the
`freeradius`/`freeradius-mysql`/`freeradius-utils`/`mysql-client` packages
and deploys `config/raddb/*` over the stock Debian/Ubuntu config paths
(`/etc/freeradius/...`, not the version-numbered `/etc/freeradius/3.2/`
path some other FreeRADIUS distributions use). `.env` (repo root) is wired
into the `freeradius` systemd service via an `EnvironmentFile=` drop-in, so
FreeRADIUS's `$ENV{...}` config references and every `scripts/*.sh` CLI
tool read the exact same values from one file.

Setup order: `scripts/install_ubuntu.sh` → `scripts/bootstrap_db.sh` →
`scripts/provision_db_users.sh` → `systemctl restart freeradius &&
freeradius -XC`. The first script deliberately does not start/verify
FreeRADIUS itself — `mods-available/sql` connects as `RADIUS_DB_USER`,
which doesn't exist in MySQL until `provision_db_users.sh` runs, which in
turn needs the schema from `bootstrap_db.sh` to exist first.

**Binary name:** on Debian/Ubuntu the daemon and CLI binary is `freeradius`
(`freeradius -X`, `freeradius -XC`), not `radiusd` — that name is used by
some other distributions/upstream builds, not this one. Every command in
this doc uses the correct Debian/Ubuntu name.

## The problem this design solves

FreeRADIUS 3.2's stock SQL schema assumes globally unique usernames — every
query filters by `username` alone. Two tenants both having a subscriber
named `budi` would collide: tenant A's `budi` could authenticate with, or
even receive reply attributes from, tenant B's rows.

## The fix: NAS-IP → tenant_id

A Mikrotik NAS device physically belongs to exactly one tenant — it never
serves two competing ISPs at once. So the source IP of an incoming RADIUS
packet already uniquely identifies the tenant, with no need to change how
subscribers are named (no `user@tenantslug` convention required).

- `nas.nasname` (the NAS's IP) stays **globally unique** and now also carries
  `tenant_id` — this is the root of the whole isolation model.
- `config/raddb/policy.d/isp_tenant` resolves `ISP-Tenant-Id` by looking up
  `Client-IP-Address` (FreeRADIUS's internal record of which client/NAS
  entry actually matched — **not** the client-supplied `NAS-IP-Address`
  attribute, which is attacker-controllable) against the `nas` table.
- Every table added in `sql/003_add_tenant_id_columns.sql` is then queried
  with `AND tenant_id = '%{control:ISP-Tenant-Id}'` — see
  `config/raddb/mods-config/sql/main/mysql/queries.conf`.
- Resolution runs independently in `authorize`, `accounting`, and
  `post-auth` (`config/raddb/sites-enabled/default`) — these are separate
  RADIUS requests, so each needs its own lookup.

**Operational constraint:** this requires each Mikrotik's IP, as seen by the
RADIUS server, to be globally unique across tenants. If tenant routers sit
behind NAT with overlapping private ranges, this breaks — route them through
a VPN hub (WireGuard/OpenVPN) with non-overlapping per-tenant address
allocation before onboarding such a tenant.

## Enforcing tenant suspension

Resolving a tenant from the NAS (above) only proves *which* tenant a request
belongs to — it says nothing about whether that tenant is allowed to operate
right now. `policy.d/isp_tenant`'s `isp_tenant_check_active` closes that gap:
it checks `tenants.status` and rejects new logins with "Tenant suspended" if
it's `suspended`.

This check is deliberately called **only from `authorize`**, not from
`accounting` or `post-auth`. A suspended tenant's subscribers who are still
mid-session must be allowed to write their `Interim-Update`/`Stop`
accounting rows — otherwise `radacct` is left with sessions that never
close, which also breaks the Simultaneous-Use concurrency check for the next
person who tries to log in. Suspension blocks *new* logins; it does not
retroactively corrupt in-flight accounting.

`tenants.status` (`trial`/`active`/`suspended`) is intentionally the single
fast column this hot-path query reads — not `tenant_subscriptions.status`
(`trialing`/`active`/`past_due`/`canceled`), which is richer billing state.
The (not yet built) billing engine is what should read
`tenant_subscriptions` and decide *when* to flip `tenants.status` to
`suspended`; RADIUS itself only ever needs that final answer, on every
single auth packet, as cheaply as possible.

## Disconnecting an already-connected subscriber (CoA/Disconnect)

RADIUS accounting only records sessions — it cannot end one. Suspending a
subscriber (or a whole tenant) only blocks their *next* login attempt;
anyone already connected stays connected until they disconnect on their own.

`scripts/disconnect_session.sh <tenant_slug> <username>` sends a real RADIUS
Disconnect-Request (RFC 5176) to force an open session offline immediately.
It looks up the subscriber's current open session in `radacct`, resolves
that NAS's secret, confirms the NAS actually belongs to the given tenant
(so a typo can never disconnect a different tenant's session), and sends
the Disconnect-Request via `radclient`, installed locally on this VM
alongside FreeRADIUS itself (`freeradius-utils`).

**Requires**, on the Mikrotik side: `/radius incoming accept=yes` (RouterOS
default CoA/Disconnect port is `3799`, which the script assumes).

**Still manual** — nothing calls this script automatically yet. Wiring
"subscription past due" or "hotspot quota exhausted" to an automatic
disconnect is future billing-engine/app-layer work; today it's an operator
(or future cron job) running this script by hand.

## Accounting → billing

`radacct` and `radpostauth` carry `tenant_id` on every row, so billing/
reporting queries filter by `tenant_id` directly. Two distinct billing
relationships exist and must not be confused:

**Platform → tenant** (you charging the ISPs that rent this platform):
`sql/006_platform_billing.sql` — `platform_plans` (the plans you sell:
price, billing cycle, subscriber/NAS limits), `tenant_subscriptions` (which
plan a tenant is on, current period, optional payment-gateway subscription
id), `platform_invoices` + `platform_invoice_items`, and `platform_payments`
(gateway-ready: `gateway`, `gateway_transaction_id`, `payment_method`,
`payment_url`, `raw_payload` for webhook reconciliation — modeled on a
Midtrans/Xendit-style integration, swappable without a schema change).
`tenants.billing_plan` (a loose text field) was dropped in this migration,
superseded by `tenant_subscriptions`.

**Tenant → its own subscribers** (an ISP charging its customers):
`sql/004_billing_seam.sql` has `service_plans` (ties a plan to a
`radgroupreply` groupname — assigning a subscriber to a plan is just
ensuring the right `radusergroup` row exists) and `tenant_subscribers`
(human/business metadata that doesn't belong in `radcheck`).
`sql/008_tenant_billing.sql` adds `subscriber_invoices` +
`subscriber_payments` (same gateway-ready shape as the platform side, but
`invoice_number` is unique per-tenant, not globally — each tenant runs its
own numbering) and `voucher_batches` for hotspot voucher sales tracking.

Convention for both: every billing table gets a `tenant_id` column, an
index on `(tenant_id, created_at)`, and a `currency` column (`IDR` default,
in case a tenant ever needs another currency).

## Users, roles, and audit (schema only — no dashboard/API built yet)

`sql/007_users_roles.sql` — a single `users` table with `role` enum
(`super_admin` / `tenant_admin` / `tenant_staff`) and nullable `tenant_id`
(`NULL` only for `super_admin`), enforced by a `CHECK` constraint. The
finer-grained split of what `tenant_staff` can/can't do (e.g. view
subscribers but not touch billing) is an application-layer concern, not
encoded in this table. `password_hash` must hold a real hash (bcrypt/
argon2) — unrelated to `radcheck.Cleartext-Password`, which is a RADIUS
protocol requirement, not a precedent for dashboard credential storage.

`sql/009_audit_log.sql` — a generic `audit_logs` table (`tenant_id`/
`user_id` both nullable, for platform-level or system/script actions)
recording `action` + `entity_type`/`entity_id` + a `metadata` JSON blob.

## Operational extras (`sql/010_operational_extras.sql`)

Three small companions to tables that already existed, not new features:

- **`nas.last_contact_at`** — updated inside `isp_tenant_resolve` itself
  (via a `%{sql: UPDATE ...}` xlat) on every authorize/accounting/post-auth
  request that resolves a NAS. Gives a cheap "is this router even online"
  signal for free — no separate heartbeat/ping mechanism needed.
- **`password_resets`** — a forgot-password flow is a day-one need for the
  `users` table (007), not a feature to bolt on later. Stores a token hash,
  never the raw token — same principle as `users.password_hash`.
- **`notifications`** — a log of reminders/alerts actually sent (invoice
  due, payment confirmed, tenant suspended), so a future billing engine can
  check "did I already send this?" and so there's an audit trail
  independent of whichever email/SMS/WhatsApp provider ends up wired in.
  `recipient_id`/`related_id` are intentionally polymorphic (no FK — a
  recipient is either a `users` row or a `tenant_subscribers` row); that
  distinction is enforced by the application, not the schema.

## Tenant billing profile & invoice immutability (`sql/011_tenant_billing_profile.sql`)

`tenants` only ever carried `slug`/`name`/`status` — not enough to legally
invoice a business in Indonesia (no NPWP, no registered billing address, no
finance contact). `tenant_billing_profiles` (1-to-1 with `tenants`) fixes
that: `legal_name`, `tax_id` (NPWP), `billing_email`/`billing_phone`,
`billing_address`, `pic_name`.

**Invoices snapshot billing details, they don't live-join them.**
`platform_invoices` gained `billing_name`/`billing_tax_id`/`billing_address`
columns populated from `tenant_billing_profiles` at the moment the invoice
is created; `subscriber_invoices` gained `billing_name`/`billing_address`
from `tenant_subscribers` the same way. An invoice is a legal record of what
was billed under what identity at that time — it must not silently change
if the tenant (or subscriber) edits their profile afterward. This is why
these are separate columns rather than always joining to the live profile
table.

**Duplicate-billing safeguard:** `platform_invoices` now has a unique
constraint on `(subscription_id, period_start)` and `subscriber_invoices` on
`(subscriber_id, period_start)` — a data-integrity backstop so a bug in the
(not-yet-built) billing engine firing twice can't double-invoice the same
period. `NULL subscription_id` (one-off/manual invoices) stays unrestricted.

## Automated recurring billing for a tenant's own subscribers (`sql/012_subscriber_subscriptions.sql`)

Mirrors `tenant_subscriptions` one level down: `subscriber_subscriptions`
tracks a subscriber's current plan, billing period, and optional
payment-gateway subscription id — for tenants who want their customers
billed automatically every cycle, not just via manual invoices or prepaid
vouchers. Same convention: current plan = the row with the latest
`current_period_end`.

`subscriber_invoices.subscription_id` (nullable) traces which subscription
generated an invoice, same pattern as `platform_invoices.subscription_id`.
`tenant_subscribers.service_plan_id` was dropped — same reasoning as
dropping `tenants.billing_plan` in `006_platform_billing.sql`: a single
"current plan" pointer can't represent plan-change history or gateway
billing state, which `subscriber_subscriptions` now owns.

## Payment gateway failure handling (`sql/013_payment_gateway_resilience.sql`)

Three real gateway failure modes the original `platform_payments`/
`subscriber_payments` shape couldn't handle:

- **Order id vs transaction id are different things, known at different
  times.** You create a payment row and send the *gateway* an order id you
  chose, before you know anything about their side. Their
  `gateway_transaction_id` only exists once they respond/webhook back — and
  their webhook is matched against the order id you originally sent, not a
  transaction id you didn't have yet. Both tables gained `gateway_order_id`
  (yours, set at creation) alongside the existing `gateway_transaction_id`
  (theirs, set once known), each with its own unique key per gateway.
- **Webhooks retry and can arrive out of order.** A single overwritable
  `raw_payload` column can't protect against a stale "pending" webhook
  arriving *after* a "settlement" one and reverting a completed payment.
  `payment_gateway_events` now logs every webhook received (polymorphic
  `payment_type`/`payment_id` across both payment tables, no FK — same
  pattern as `notifications`), so application logic can apply only
  forward-moving status transitions and there's a trail when reconciliation
  disagrees with the gateway's dashboard.
- **Refunds aren't a single boolean, and chargebacks aren't refunds.**
  `payment_refunds` tracks amount/reason/gateway-refund-id per refund
  (partial refunds happen more than once); `chargeback` was added to both
  payment `status` enums as its own state, distinct from a
  merchant-initiated refund.

`gateway_fee` was also added to both payment tables — the platform's actual
net revenue (for reporting) is `amount - gateway_fee`, not the gross charge.

## Reporting gaps (`sql/014_reporting_extras.sql`)

- **`cancellation_reason`** added to `tenant_subscriptions` and
  `subscriber_subscriptions` — a churn report needs to know *why*, not just
  *when*, and there was nowhere to record that.
- **`vouchers`** — `voucher_batches` only ever recorded "generated 200
  vouchers for X", with no link down to which actual `radcheck` credentials
  came from that batch and no record of whether/when each was used. Without
  this table, "sold vs redeemed" is unanswerable. Wired into
  `policy.d/isp_voucher`'s `isp_voucher_mark_redeemed`, called from the
  Access-Accept path of `post-auth` only (never from `Post-Auth-Type
  REJECT`) — a failed login must not count as a redemption. It's a
  harmless no-op for PPPoE subscribers, who never have a row in `vouchers`
  in the first place.

**Deliberately not added:** pre-aggregated revenue rollup tables and NAS
uptime history. At the target scale (tens–low hundreds of tenants), revenue
and AR-aging reports compute directly from `platform_invoices`/
`subscriber_invoices` fast enough without a materialized rollup — adding
one now would be optimizing for a scale this platform isn't at yet.

## Mikrotik offline/reconnect behavior

Two distinct failure modes when a tenant's Mikrotik drops off the network,
neither of which the base design handled:

**Zombie sessions.** A network blip or power loss on the Mikrotik sends
FreeRADIUS nothing — no Accounting-Off, no final Interim-Update. The
`accounting-on`/`accounting-off` handling in `queries.conf` (which closes
out sessions when a NAS announces a reboot) is a bonus if it fires, **not a
guarantee** — RouterOS is not reliable about sending Accounting-On when it
comes back up. Left alone, these rows sit in `radacct` with
`acctstoptime IS NULL` forever, which poisons the Simultaneous-Use check
(a subscriber capped at one concurrent session can look permanently
"still connected" and be unable to log back in) and makes any future
"who's online now" report lie.

`scripts/cleanup_stale_sessions.sh [stale_minutes]` (default 15 minutes —
3x the common `interim-update=5m` Mikrotik setting) sweeps and closes any
session that's stopped updating, tagging it `acctterminatecause =
'Stale-Session-Cleanup'` so it's distinguishable from a real NAS-reported
cause. `sql/015_stale_session_index.sql` adds the
`(acctstoptime, acctupdatetime)` index this sweep needs — none of
`radacct`'s other indexes (keyed off username/tenant first) serve an
all-tenants "which open sessions haven't updated recently" scan. **This is
a sweep meant to run on a schedule** (cron / a future app-layer job), not a
one-off fix.

**NAS IP changes on reconnect.** Tenant resolution is entirely IP-based
(see above) — if a Mikrotik comes back with a different IP than it
registered with (dynamic WAN reassignment, or it moved to a new VPN tunnel
address), it instantly becomes an "Unrecognized NAS" and every subscriber
on that router is locked out until `nas.nasname` is corrected.
`scripts/update_nas_ip.sh <tenant_slug> <shortname> <new_ip>` fixes this —
identifies the NAS by its stable `shortname` rather than the old IP (which
is the very thing that just changed, so the operator may not remember it
exactly).

## Data/access security

**Least-privilege DB users.** FreeRADIUS itself now runs as a dedicated
`RADIUS_DB_USER` (`scripts/provision_db_users.sh`), not the general-purpose
`MYSQL_USER` that `scripts/bootstrap_db.sh` and every other CLI script use.
The grants are scoped to exactly what `queries.conf`/`policy.d/{isp_tenant,
isp_voucher}` touch: read-only on `radcheck`/`radreply`/`radgroupcheck`/
`radgroupreply`/`radusergroup`/`tenants`; read-write on `radacct`/`nas`/
`vouchers`; insert-only on `radpostauth`. **No grant at all** — not even
`SELECT` — on any billing, user, or audit table (`platform_*`,
`subscriber_*`, `users`, `password_resets`, `audit_logs`, `notifications`,
`tenant_billing_profiles`, `service_plans`, `voucher_batches`). If the
FreeRADIUS process or its config is ever compromised, the blast radius
stops at RADIUS-core tables instead of the entire database. Run this script
after `bootstrap_db.sh` (GRANTing on a table requires it to exist) and
again after any migration changes what FreeRADIUS itself reads/writes.

**SQL escaping in `scripts/*.sh`.** These CLI tools build SQL strings from
their arguments by hand (the `mysql -e` flag has no parameterized-query
option). Every interpolated value now goes through a `sql_escape()` helper
that escapes backslash *before* quote — escaping quote alone leaves a
trailing backslash free to swallow the closing quote it should have
protected. `cleanup_stale_sessions.sh`'s numeric argument is validated as
digits-only before reaching SQL at all, for the same reason.

**MySQL's own firewall/bind-address is the actual boundary now.** With
MySQL on a separate server reached over a real network, restricting who
can reach port 3306 is that server's job (firewall rules allowing only the
FreeRADIUS VM's IP, `bind-address` not set to `0.0.0.0` unless genuinely
needed) — nothing in this repo controls that. `scripts/provision_db_users.sh`
does its part by scoping `RADIUS_DB_USER`'s grant to `RADIUS_VM_IP`
specifically rather than `'%'` (any host), so even a leaked password
doesn't grant access from an arbitrary IP.

**FreeRADIUS never touches raw card data.** `platform_payments`/
`subscriber_payments` store only gateway references (`gateway_order_id`,
`gateway_transaction_id`, `payment_url`) — actual card/e-wallet details
stay inside the gateway's own PCI-DSS-compliant infrastructure and never
reach this database. This is a deliberate scope boundary, not an
oversight: keep it that way when the app layer is built — never let a card
number or CVV touch this schema.

**Not yet addressed, flagged for later:**
- **Transport encryption to MySQL.** No TLS configured between the
  FreeRADIUS VM and the separate MySQL server — this traffic (including
  `RADIUS_DB_USER`'s password on connect, and every query result) crosses
  a real network in plaintext. This is a genuine gap given the actual
  topology (not a low-risk single-host Docker bridge) — enable
  `tls_ca_file`/`tls_check_cert` in `mods-enabled/sql`, or put the link
  between the two VMs on a private network/VPN.
- **RADIUS-over-UDP is inherently only partially encrypted** (the
  shared-secret scheme obfuscates `User-Password`, not the whole packet) —
  this is a protocol-level property of RADIUS/Mikrotik, not something this
  schema can fix. The VPN-hub recommendation for CGNAT tenants (see above)
  doubles as mitigation here too: it puts NAS↔server traffic on a private
  tunnel instead of the open internet.
- **Personal data retention (Indonesia's UU PDP).** `tenant_subscribers`
  holds subscriber PII (name, phone, address) with no retention/erasure
  policy or anonymization mechanism yet. This is a product/legal decision
  as much as a schema one — flagged here so it isn't forgotten, not solved.

## Subscriber profile completeness (`sql/016_tenant_subscriber_details.sql`)

`tenant_subscribers` gained `email`, `identity_type`/`identity_number`
(KTP by default, `identity_type` exists so a foreign subscriber's passport
doesn't have to lie about being a KTP), and `install_lat`/`install_lng`
(a GPS pin is what a field technician actually navigates by — a text
`address` alone isn't enough once a tenant has real installation volume).

**The RADIUS credential and the human profile are now an actual foreign
key, not a string-matching coincidence.** `radcheck`/`radreply` gained a
nullable `subscriber_id` referencing `tenant_subscribers(id)` — nullable
because `vouchers` (sql/014) are intentionally anonymous prepaid
credentials with no human profile behind them at all. FreeRADIUS itself
never dereferences this column (no query in `queries.conf` joins to
`tenant_subscribers`), which is deliberate: it means subscriber PII (KTP,
email, GPS) stays completely unreachable from the RADIUS-core DB account
(see `scripts/provision_db_users.sh`) even though the tables are now
formally linked.

## Per-tenant integrations (`sql/017_tenant_integrations.sql`)

Each tenant bills its own subscribers through **its own** payment gateway
account and messages them from **its own** WhatsApp number — not the
platform's. `tenant_integrations` stores this: `integration_type`
(`payment_gateway`/`whatsapp`/`sms`/`email`), `provider` (`midtrans` |
`xendit` | `fonnte` | `starsender` | `smtp` | ...), and a `credentials` JSON
blob (field shape differs per provider — Midtrans wants
`server_key`/`client_key`, Fonnte wants `token`/`device`). One active
config per channel type per tenant; switching providers (Fonnte to
Starsender) updates the row rather than adding a second one.

This is distinct from `platform_payments`' gateway (sql/006) — that's the
*platform's own* merchant account for billing tenants, a single
platform-wide credential that belongs in `.env`/app config, not a
per-tenant table, since there's only one platform.

**Security:** `credentials` holds live API keys/tokens in plaintext (same
necessity as `nas.secret`). This table gets zero grants in
`scripts/provision_db_users.sh` — the RADIUS-core service account has no
reason to ever read it. `notifications` gained a `provider` column (which
provider actually sent it) for lightweight traceability — not a full
immutable snapshot like invoices get, since a notification log isn't a
legal financial record.

## Deferred to later phases (not implemented yet)

- **The dashboard/API itself.** All of the above (billing, users, audit) is
  schema only — no application layer reads or writes these tables yet.
  Tenant/NAS management is still purely `scripts/*.sh` + direct SQL.
- **True dynamic NAS onboarding.** `read_clients=yes` (currently used) loads
  the `nas` table only at FreeRADIUS startup — adding a NAS requires a HUP
  (`scripts/reload_freeradius.sh`). A later phase should switch to
  FreeRADIUS's per-packet dynamic-clients virtual server
  (`sites-available/dynamic-clients`) for zero-restart self-service
  onboarding.
- **Production hardening** — `radacct` archiving strategy, automated MySQL
  backups (the separate MySQL server's responsibility), TLS between the
  FreeRADIUS VM and MySQL, a CI step running `freeradius -XC` on every config
  change before it's deployed via `scripts/install_ubuntu.sh`.
- **Realm-suffix routing** (`user@tenantslug` via the `suffix` module) as
  defense-in-depth for edge cases like a reseller aggregating multiple
  downstream tenants behind one shared upstream NAS. Not needed for the
  primary model.

## Verifying tenant isolation locally

`sql/005_seed_dev_data.sql` seeds two tenants, each with a subscriber
literally named `budi` with a different password, mapped to two different
NAS IPs (`10.99.0.101` / `10.99.0.102`). To prove isolation, requests need
to actually arrive from those two different source IPs — on a single
Ubuntu VM (no Docker network to fake this with), Linux network namespaces
do the same job: each namespace gets its own IP via a veth pair, so a
`radtest` run inside it hits FreeRADIUS with that IP as the source address,
exactly like a second physical Mikrotik would.

```sh
scripts/bootstrap_db.sh   # applies sql/001..005 including the seed data

# Two namespaces, each with a point-to-point veth link to the host —
# no routing/NAT needed, both ends sit in the same /24 per pair.
sudo ip netns add ns-tenant-a
sudo ip link add veth-a type veth peer name veth-a-ns
sudo ip link set veth-a-ns netns ns-tenant-a
sudo ip addr add 10.99.0.1/24 dev veth-a
sudo ip link set veth-a up
sudo ip netns exec ns-tenant-a ip addr add 10.99.0.101/24 dev veth-a-ns
sudo ip netns exec ns-tenant-a ip link set veth-a-ns up
sudo ip netns exec ns-tenant-a ip link set lo up

sudo ip netns add ns-tenant-b
sudo ip link add veth-b type veth peer name veth-b-ns
sudo ip link set veth-b-ns netns ns-tenant-b
sudo ip addr add 10.99.0.2/24 dev veth-b
sudo ip link set veth-b up
sudo ip netns exec ns-tenant-b ip addr add 10.99.0.102/24 dev veth-b-ns
sudo ip netns exec ns-tenant-b ip link set veth-b-ns up
sudo ip netns exec ns-tenant-b ip link set lo up

# Tenant A's budi, from tenant A's NAS IP — should succeed:
sudo ip netns exec ns-tenant-a radtest budi tenant-a-password 10.99.0.1 0 tenant-a-secret

# Tenant B's budi, from tenant B's NAS IP — should succeed with ITS OWN password:
sudo ip netns exec ns-tenant-b radtest budi tenant-b-password 10.99.0.2 0 tenant-b-secret

# The actual isolation proof — tenant A's password from tenant B's NAS
# must be REJECTED:
sudo ip netns exec ns-tenant-b radtest budi tenant-a-password 10.99.0.2 0 tenant-b-secret

# Cleanup (also removes the paired veth-a/veth-b on the host side):
sudo ip netns del ns-tenant-a
sudo ip netns del ns-tenant-b
```

Then check `mysql -h "$MYSQL_HOST" -u "$MYSQL_USER" -p "$MYSQL_DATABASE" -e "SELECT tenant_id, username FROM radpostauth ORDER BY authdate DESC LIMIT 5;"`
to confirm each accepted request wrote the correct `tenant_id`.

Simpler alternative if `ip netns` feels like overkill: skip the namespaces
and just test with two real Mikrotik routers (or two VMs) on the LAN,
registered with their real IPs — the isolation logic being tested is
identical either way.
