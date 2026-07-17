-- Two gaps that would otherwise make specific reports impossible to
-- produce from this schema at all, not just inconvenient.

-- Churn/cancellation reports need to know WHY, not just when.
ALTER TABLE tenant_subscriptions
  ADD COLUMN cancellation_reason varchar(255) DEFAULT NULL AFTER canceled_at;

ALTER TABLE subscriber_subscriptions
  ADD COLUMN cancellation_reason varchar(255) DEFAULT NULL AFTER canceled_at;

-- voucher_batches (008) only records batch-level metadata (quantity sold,
-- price) — there was no link from that batch down to the actual
-- radcheck/radreply credentials it generated, and no record of whether or
-- when each individual voucher was ever redeemed. Without this table,
-- "how many of these 200 vouchers were actually used" is unanswerable.
-- username matches the corresponding radcheck.username for this tenant —
-- not FK'd to radcheck (that table has no primary key suited for it and
-- isn't tenant-uniquely-keyed on username alone), enforced by application
-- logic when a voucher is generated.
CREATE TABLE vouchers (
  id           bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  batch_id     bigint unsigned NOT NULL,
  tenant_id    bigint unsigned NOT NULL,
  username     varchar(64) NOT NULL,
  status       enum('unused','active','expired') NOT NULL DEFAULT 'unused',
  redeemed_at  timestamp NULL DEFAULT NULL,
  created_at   timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY vouchers_tenant_username (tenant_id, username),
  KEY vouchers_batch (batch_id),
  CONSTRAINT fk_vouchers_batch FOREIGN KEY (batch_id) REFERENCES voucher_batches(id) ON DELETE CASCADE,
  CONSTRAINT fk_vouchers_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
