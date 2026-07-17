-- Fixes a real gap: `tenants` only carries slug/name/status, which isn't
-- enough to legally invoice a business in Indonesia (needs NPWP + a
-- registered billing address for a proper Faktur Pajak). Also adds invoice
-- immutability (snapshot billing details at issuance, not a live join) and
-- a data-integrity safeguard against accidentally double-billing a period.

-- 1-to-1 with tenants — separate table (not columns on tenants) because
-- this is billing-specific profile data, not core tenant identity.
CREATE TABLE tenant_billing_profiles (
  tenant_id        bigint unsigned NOT NULL PRIMARY KEY,
  legal_name       varchar(255) NOT NULL, -- registered business name; may differ from tenants.name (a trade name)
  tax_id           varchar(32) DEFAULT NULL, -- NPWP
  billing_email    varchar(255) DEFAULT NULL,
  billing_phone    varchar(32) DEFAULT NULL,
  billing_address  varchar(500) DEFAULT NULL,
  pic_name         varchar(255) DEFAULT NULL, -- finance/PIC contact person
  created_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_tenant_billing_profiles_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Snapshot columns: populated from tenant_billing_profiles at the moment an
-- invoice is created, then never touched again. An invoice is a legal
-- record of what was billed under what identity at that time — it must not
-- silently change if the tenant later edits their billing profile.
ALTER TABLE platform_invoices
  ADD COLUMN billing_name    varchar(255) DEFAULT NULL AFTER tenant_id,
  ADD COLUMN billing_tax_id  varchar(32)  DEFAULT NULL AFTER billing_name,
  ADD COLUMN billing_address varchar(500) DEFAULT NULL AFTER billing_tax_id;

-- Same immutability reasoning for the tenant's own subscribers: their
-- name/address on tenant_subscribers can change, but an already-issued
-- invoice shouldn't retroactively change with it.
ALTER TABLE subscriber_invoices
  ADD COLUMN billing_name    varchar(255) DEFAULT NULL AFTER subscriber_id,
  ADD COLUMN billing_address varchar(500) DEFAULT NULL AFTER billing_name;

-- Data-integrity safeguard: a subscription can have at most one invoice per
-- billing period, even if the (not-yet-built) billing engine has a bug and
-- fires twice. NULL subscription_id (one-off/manual invoices) stays
-- unrestricted — MySQL unique indexes treat each NULL as distinct.
ALTER TABLE platform_invoices
  ADD UNIQUE KEY platform_invoices_subscription_period (subscription_id, period_start);

ALTER TABLE subscriber_invoices
  ADD UNIQUE KEY subscriber_invoices_subscriber_period (subscriber_id, period_start);
