-- Per-tenant third-party credentials — payment gateway (Midtrans/Xendit)
-- AND notification channels (Fonnte/Starsender for WhatsApp, SMS, SMTP for
-- email). Each tenant is its own merchant/sender: a tenant bills its
-- subscribers through ITS OWN gateway account, and messages them from ITS
-- OWN WhatsApp number — not the platform's. That keeps the platform out of
-- ever touching or transmitting a tenant's subscriber's money directly
-- (platform_payments, a separate concern, is the platform's own gateway
-- account for billing tenants — see sql/006_platform_billing.sql).
--
-- credentials is JSON because every provider needs different fields
-- (Midtrans: server_key/client_key; Xendit: secret_key/callback_token;
-- Fonnte/Starsender: token/device) — same reasoning as the JSON payload
-- columns in sql/013_payment_gateway_resilience.sql.
--
-- SECURITY: this table holds live API keys/tokens in plaintext (same
-- necessity as nas.secret). It intentionally gets ZERO grants in
-- scripts/provision_db_users.sh — the RADIUS-core service account has no
-- reason to ever read it and never will.
CREATE TABLE tenant_integrations (
  id                bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id         bigint unsigned NOT NULL,
  integration_type  enum('payment_gateway','whatsapp','sms','email') NOT NULL,
  provider          varchar(64) NOT NULL, -- 'midtrans' | 'xendit' | 'fonnte' | 'starsender' | 'smtp' | ...
  credentials       json NOT NULL,
  is_active         tinyint(1) NOT NULL DEFAULT 1,
  created_at        timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  -- One active config per channel type per tenant — switching providers
  -- (Fonnte to Starsender) updates this row rather than adding a second one.
  UNIQUE KEY tenant_integrations_tenant_type (tenant_id, integration_type),
  CONSTRAINT fk_tenant_integrations_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Lightweight traceability only (not a full snapshot like invoices get —
-- notifications is a log, not a legal financial record): which provider
-- actually sent this, in case a tenant switches providers later and a
-- delivery issue needs investigating.
ALTER TABLE notifications
  ADD COLUMN provider varchar(64) DEFAULT NULL AFTER channel;
