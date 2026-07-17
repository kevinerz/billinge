-- Billing the PLATFORM charges a TENANT for renting this SaaS (distinct from
-- sql/004_billing_seam.sql, which is a tenant billing ITS OWN subscribers).
--
-- Payment model: automatic via a payment gateway (Midtrans/Xendit-style) —
-- gateway/gateway_transaction_id/payment_url/raw_payload carry whatever that
-- integration needs. Swapping gateways later only touches the app layer that
-- writes these columns, not the schema.

CREATE TABLE platform_plans (
  id               bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  slug             varchar(64) NOT NULL UNIQUE,
  name             varchar(100) NOT NULL,
  price            decimal(14,2) NOT NULL,
  currency         char(3) NOT NULL DEFAULT 'IDR',
  billing_cycle    enum('monthly','yearly') NOT NULL DEFAULT 'monthly',
  max_subscribers  int unsigned DEFAULT NULL, -- NULL = unlimited
  max_nas          int unsigned DEFAULT NULL, -- NULL = unlimited
  is_active        tinyint(1) NOT NULL DEFAULT 1,
  created_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- One row per subscription period/plan-change; a tenant's CURRENT plan is
-- whichever row has the latest current_period_end (or status='active' with
-- no successor) — no separate "is_current" flag needed.
CREATE TABLE tenant_subscriptions (
  id                       bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id                bigint unsigned NOT NULL,
  platform_plan_id         bigint unsigned NOT NULL,
  status                   enum('trialing','active','past_due','canceled') NOT NULL DEFAULT 'trialing',
  current_period_start     date NOT NULL,
  current_period_end       date NOT NULL,
  gateway                  varchar(32) DEFAULT NULL,
  gateway_subscription_id  varchar(128) DEFAULT NULL,
  canceled_at              timestamp NULL DEFAULT NULL,
  created_at               timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at               timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY tenant_subscriptions_tenant (tenant_id, current_period_end),
  CONSTRAINT fk_tenant_subscriptions_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  CONSTRAINT fk_tenant_subscriptions_plan FOREIGN KEY (platform_plan_id) REFERENCES platform_plans(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE platform_invoices (
  id               bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id        bigint unsigned NOT NULL,
  subscription_id  bigint unsigned DEFAULT NULL,
  invoice_number   varchar(32) NOT NULL UNIQUE, -- single issuer (the platform) -> globally unique
  currency         char(3) NOT NULL DEFAULT 'IDR',
  subtotal         decimal(14,2) NOT NULL DEFAULT 0,
  tax_amount       decimal(14,2) NOT NULL DEFAULT 0, -- PPN
  total_amount     decimal(14,2) NOT NULL,
  status           enum('draft','pending','paid','overdue','void') NOT NULL DEFAULT 'draft',
  period_start     date NOT NULL,
  period_end       date NOT NULL,
  due_date         date NOT NULL,
  paid_at          timestamp NULL DEFAULT NULL,
  created_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY platform_invoices_tenant_created (tenant_id, created_at),
  CONSTRAINT fk_platform_invoices_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  CONSTRAINT fk_platform_invoices_subscription FOREIGN KEY (subscription_id) REFERENCES tenant_subscriptions(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE platform_invoice_items (
  id           bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  invoice_id   bigint unsigned NOT NULL,
  description  varchar(255) NOT NULL,
  quantity     int unsigned NOT NULL DEFAULT 1,
  unit_price   decimal(14,2) NOT NULL,
  amount       decimal(14,2) NOT NULL,
  KEY platform_invoice_items_invoice (invoice_id),
  CONSTRAINT fk_platform_invoice_items_invoice FOREIGN KEY (invoice_id) REFERENCES platform_invoices(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE platform_payments (
  id                      bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  invoice_id              bigint unsigned NOT NULL,
  tenant_id               bigint unsigned NOT NULL,
  gateway                 varchar(32) NOT NULL,           -- 'midtrans' | 'xendit' | ...
  gateway_transaction_id  varchar(128) DEFAULT NULL,
  payment_method          varchar(32) DEFAULT NULL,       -- 'bank_transfer' | 'credit_card' | 'e_wallet' | 'qris'
  payment_url             varchar(512) DEFAULT NULL,
  amount                  decimal(14,2) NOT NULL,
  currency                char(3) NOT NULL DEFAULT 'IDR',
  status                  enum('pending','settlement','expired','failed','refunded') NOT NULL DEFAULT 'pending',
  raw_payload             json DEFAULT NULL, -- last webhook payload, kept for reconciliation/debugging
  paid_at                 timestamp NULL DEFAULT NULL,
  created_at              timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at              timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY platform_payments_invoice (invoice_id),
  KEY platform_payments_tenant_created (tenant_id, created_at),
  UNIQUE KEY platform_payments_gateway_txn (gateway, gateway_transaction_id),
  CONSTRAINT fk_platform_payments_invoice FOREIGN KEY (invoice_id) REFERENCES platform_invoices(id),
  CONSTRAINT fk_platform_payments_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Superseded by tenant_subscriptions -> platform_plans above.
ALTER TABLE tenants DROP COLUMN billing_plan;
