-- Two gaps in the subscriber profile itself, plus a structural link that
-- was always implicit (matched by username string only) and should be an
-- actual foreign key.

ALTER TABLE tenant_subscribers
  ADD COLUMN email             varchar(255) DEFAULT NULL AFTER phone,
  -- KTP by default (Indonesia's national ID) but identity_type keeps this
  -- from breaking the day a tenant needs to register a foreign subscriber
  -- (passport) — same principle as tenant_billing_profiles.tax_id being
  -- optional rather than assuming every tenant has one.
  ADD COLUMN identity_type     enum('ktp','other') NOT NULL DEFAULT 'ktp' AFTER email,
  ADD COLUMN identity_number   varchar(32) DEFAULT NULL AFTER identity_type,
  -- Installation address commonly differs from the generic `address`
  -- already on this table once a tenant has both residential and business
  -- subscribers; GPS pin is what a field technician actually navigates by,
  -- not a text address. Both nullable — not every tenant will fill these.
  ADD COLUMN install_lat       decimal(10,7) DEFAULT NULL AFTER address,
  ADD COLUMN install_lng       decimal(10,7) DEFAULT NULL AFTER install_lat;

-- The RADIUS credential (radcheck/radreply, matched by username) and the
-- human profile (tenant_subscribers) were only ever connected by both
-- happening to hold the same username string for the same tenant_id — no
-- actual foreign key. Nullable: vouchers (sql/014) are intentionally
-- anonymous prepaid credentials with no subscriber profile at all, so not
-- every radcheck/radreply row has one of these.
ALTER TABLE radcheck
  ADD COLUMN subscriber_id bigint unsigned DEFAULT NULL AFTER tenant_id,
  ADD CONSTRAINT fk_radcheck_subscriber FOREIGN KEY (subscriber_id) REFERENCES tenant_subscribers(id) ON DELETE SET NULL;

ALTER TABLE radreply
  ADD COLUMN subscriber_id bigint unsigned DEFAULT NULL AFTER tenant_id,
  ADD CONSTRAINT fk_radreply_subscriber FOREIGN KEY (subscriber_id) REFERENCES tenant_subscribers(id) ON DELETE SET NULL;
