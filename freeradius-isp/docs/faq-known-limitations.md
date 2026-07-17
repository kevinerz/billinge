# FAQ / Known Limitations

**Q: Can two tenants have a subscriber with the same username?**
Yes — this was the core problem this design solves. Every RADIUS query is
scoped by `tenant_id`, resolved from the NAS's source IP, so `budi@tenant-a`
and `budi@tenant-b` never collide. See [architecture.md](architecture.md).

**Q: I added a NAS with `scripts/add_nas.sh` but it's not authenticating.**
`read_clients=yes` loads the `nas` table only at FreeRADIUS startup. Run
`scripts/reload_freeradius.sh` (sends HUP) after adding or editing a NAS.
This is a deliberate Phase-1/2 limitation — a later phase switches to
FreeRADIUS's dynamic-clients virtual server, which does a live per-packet
SQL lookup with no restart needed.

**Q: A tenant's Mikrotik is behind CGNAT / has no stable public IP.**
Tenant resolution depends on each NAS's IP, as seen by the RADIUS server,
being globally unique across all tenants. If a tenant's router sits behind
NAT with a private/overlapping IP, route it through a VPN hub (WireGuard/
OpenVPN) with non-overlapping per-tenant address allocation, and register
the VPN-assigned IP as the NAS IP instead of the router's LAN/WAN IP.

**Q: Why NAS-IP-based tenant resolution instead of `user@tenantslug`
realm-suffix usernames?**
A Mikrotik physically belongs to one tenant, so the NAS IP already
identifies the tenant with no changes needed to how subscribers are named
or how existing Mikrotik PPP/hotspot configs work. Realm-suffix routing
(FreeRADIUS's `suffix` module) is available as defense-in-depth for a
reseller-of-resellers scenario, but isn't implemented in this phase.

**Q: Is `nas.secret` encrypted at rest?**
No — FreeRADIUS reads it in plaintext from the `nas` table by design (it
needs the plaintext to compute/verify RADIUS packet authenticators). Treat
database access to the `nas` and `radcheck` tables (which also holds
`Cleartext-Password`) as a credential-handling boundary: restrict who can
query the production database directly.

**Q: Why is `radacct`/`radpostauth` not `ON DELETE CASCADE` when a tenant is
deleted?**
Accounting/auth-log data is an audit trail and should not silently
disappear when a tenant is offboarded. Deleting a tenant with existing
`radacct`/`radpostauth` rows will be rejected by the foreign key until those
rows are deliberately archived or purged.

**Q: What happens if a NAS sends a packet from an IP not in the `nas`
table?**
`policy.d/isp_tenant` rejects it immediately with "Unrecognized NAS - no
tenant mapping" — before any tenant-scoped table is queried.

**Q: I suspended a tenant (`tenants.status = 'suspended'`) but their
subscribers are still online.**
Expected — suspension blocks *new* logins (`isp_tenant_check_active` in
`policy.d/isp_tenant`) but RADIUS accounting alone can't end a session that's
already open. Run `scripts/disconnect_session.sh <tenant_slug> <username>`
to force an open session offline immediately via RADIUS Disconnect-Request.
See [architecture.md](architecture.md#disconnecting-an-already-connected-subscriber-coadisconnect).

**Q: `scripts/disconnect_session.sh` isn't disconnecting anything on the
Mikrotik.**
Check `/radius incoming accept=yes` is set on that router — RouterOS ignores
CoA/Disconnect-Request packets by default. Also confirm the router listens
on port `3799` (RouterOS default, which the script assumes).

**Q: A Mikrotik crashed/lost power and its subscribers still show as online
in `radacct`.**
Expected — a silent failure sends no Accounting-Off, and RouterOS isn't
reliable about sending Accounting-On when it comes back up either, so
nothing automatically closes those sessions. Run
`scripts/cleanup_stale_sessions.sh` (schedule it — this is meant to run
periodically, not once) to close sessions that have stopped updating. See
[architecture.md](architecture.md#mikrotik-offlinereconnect-behavior).

**Q: A tenant's subscribers all suddenly get "Unrecognized NAS" after their
Mikrotik reconnects.**
The router almost certainly came back with a different IP than it
registered with (dynamic WAN reassignment, VPN re-tunnel). Tenant
resolution is entirely IP-based, so `nas.nasname` has to match exactly. Fix
with `scripts/update_nas_ip.sh <tenant_slug> <shortname> <new_ip>`, then
`scripts/reload_freeradius.sh`.

**Q: Why does FreeRADIUS use a different MySQL user (`RADIUS_DB_USER`) than
the CLI scripts (`MYSQL_USER`)?**
Least privilege. FreeRADIUS only ever needs RADIUS-core tables — it has no
legitimate reason to ever read `users.password_hash` or any billing table,
so its DB account can't, even in the event the process or its config is
compromised. See `scripts/provision_db_users.sh` and
[architecture.md](architecture.md#dataaccess-security).

**Q: I ran `scripts/provision_db_users.sh` and got a MySQL error about the
table not existing.**
Run `scripts/bootstrap_db.sh` first — `GRANT ... ON database.specific_table`
requires that table to already exist.
