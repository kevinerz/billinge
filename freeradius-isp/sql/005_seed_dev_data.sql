-- Dev/test-only seed data. This is the acceptance test for tenant isolation:
-- two tenants each have a subscriber literally named "budi" with different
-- passwords and different reply attributes. If isolation is broken, tenant
-- A's password will authenticate against tenant B's NAS (or vice versa).
--
-- NAS IPs (10.99.0.101 / .102) are addresses used by the two Linux network
-- namespaces set up in docs/architecture.md's isolation test — each
-- namespace sends its radclient request from a different source IP,
-- simulating two separate Mikrotik routers on one Ubuntu VM.

INSERT INTO tenants (id, slug, name, status) VALUES
  (1, 'tenant-a', 'Tenant A (dev)', 'active'),
  (2, 'tenant-b', 'Tenant B (dev)', 'active');

-- One Mikrotik NAS per tenant. secret is a per-NAS random value in
-- production (see scripts/add_nas.sh); fixed here for reproducible dev/test.
INSERT INTO nas (tenant_id, nasname, shortname, type, secret, description) VALUES
  (1, '10.99.0.101', 'tenant-a-mikrotik-1', 'other', 'tenant-a-secret', 'Tenant A dev test NAS'),
  (2, '10.99.0.102', 'tenant-b-mikrotik-1', 'other', 'tenant-b-secret', 'Tenant B dev test NAS');

-- Same username ("budi") in both tenants, different passwords/reply attrs.
INSERT INTO radcheck (tenant_id, username, attribute, op, value) VALUES
  (1, 'budi', 'Cleartext-Password', ':=', 'tenant-a-password'),
  (2, 'budi', 'Cleartext-Password', ':=', 'tenant-b-password');

INSERT INTO radreply (tenant_id, username, attribute, op, value) VALUES
  (1, 'budi', 'Mikrotik-Rate-Limit', ':=', '5M/5M'),
  (2, 'budi', 'Mikrotik-Rate-Limit', ':=', '10M/10M');
