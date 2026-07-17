-- Closes real gaps in how the schema handles payment gateway failure modes
-- (Midtrans/Xendit-style). Applies identically to platform_payments (006)
-- and subscriber_payments (008).

-- gateway_order_id vs gateway_transaction_id — these are NOT the same
-- thing and the earlier schema only had the second one. You create a
-- payment record and send the GATEWAY an order id YOU chose before you
-- know anything about their side; gateway_transaction_id only becomes
-- known once they respond/webhook back. Webhooks are matched on the order
-- id you originally sent, not on a transaction id you didn't have yet.
ALTER TABLE platform_payments
  ADD COLUMN gateway_order_id varchar(128) DEFAULT NULL AFTER invoice_id,
  ADD COLUMN gateway_fee      decimal(14,2) DEFAULT NULL AFTER amount,
  ADD UNIQUE KEY platform_payments_gateway_order (gateway, gateway_order_id),
  MODIFY COLUMN status enum('pending','settlement','expired','failed','refunded','chargeback') NOT NULL DEFAULT 'pending';

ALTER TABLE subscriber_payments
  ADD COLUMN gateway_order_id varchar(128) DEFAULT NULL AFTER invoice_id,
  ADD COLUMN gateway_fee      decimal(14,2) DEFAULT NULL AFTER amount,
  ADD UNIQUE KEY subscriber_payments_gateway_order (gateway, gateway_order_id),
  MODIFY COLUMN status enum('pending','settlement','expired','failed','refunded','chargeback') NOT NULL DEFAULT 'pending';

-- Full webhook history, not just "the last one". A single overwritable
-- raw_payload column (as platform_payments/subscriber_payments had) can't
-- protect against a real failure mode: gateways retry webhook delivery,
-- and a stale/reordered "pending" notification arriving AFTER a
-- "settlement" one must never be allowed to revert a completed payment.
-- Keeping every event lets application logic apply only forward-moving
-- status transitions and gives a debugging trail when reconciliation goes
-- wrong. payment_type/payment_id are polymorphic (platform_payments or
-- subscriber_payments) — no FK, same pattern as notifications (010).
CREATE TABLE payment_gateway_events (
  id               bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  payment_type     enum('platform','subscriber') NOT NULL,
  payment_id       bigint unsigned NOT NULL,
  gateway          varchar(32) NOT NULL,
  event_type       varchar(64) DEFAULT NULL,   -- e.g. 'payment.settlement', 'payment.expire'
  status_reported  varchar(32) DEFAULT NULL,   -- the raw status string the gateway sent, before interpretation
  payload          json NOT NULL,
  received_at      timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY payment_gateway_events_payment (payment_type, payment_id, received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Partial refunds and chargebacks aren't a single boolean — a payment can
-- be partially refunded more than once, each with its own reason and
-- gateway-side refund id. Same polymorphic pattern as above.
CREATE TABLE payment_refunds (
  id                 bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  payment_type       enum('platform','subscriber') NOT NULL,
  payment_id         bigint unsigned NOT NULL,
  amount             decimal(14,2) NOT NULL,
  reason             varchar(255) DEFAULT NULL,
  gateway_refund_id  varchar(128) DEFAULT NULL,
  status             enum('pending','completed','failed') NOT NULL DEFAULT 'pending',
  created_at         timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY payment_refunds_payment (payment_type, payment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
