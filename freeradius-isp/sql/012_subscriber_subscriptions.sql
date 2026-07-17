-- Mirrors tenant_subscriptions (006) one level down: a tenant's own
-- subscribers can now have automated recurring billing (gateway-managed
-- subscription, not just a manually-generated invoice) if the tenant wants
-- their customers to pay automatically every cycle instead of via vouchers
-- or manual invoicing.
--
-- One row per subscription period/plan-change, same convention as
-- tenant_subscriptions: the subscriber's CURRENT plan is whichever row has
-- the latest current_period_end (or status='active' with no successor).
CREATE TABLE subscriber_subscriptions (
  id                       bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id                bigint unsigned NOT NULL,
  subscriber_id            bigint unsigned NOT NULL,
  service_plan_id          bigint unsigned NOT NULL,
  status                   enum('trialing','active','past_due','canceled') NOT NULL DEFAULT 'trialing',
  current_period_start     date NOT NULL,
  current_period_end       date NOT NULL,
  gateway                  varchar(32) DEFAULT NULL,
  gateway_subscription_id  varchar(128) DEFAULT NULL,
  canceled_at              timestamp NULL DEFAULT NULL,
  created_at               timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at               timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY subscriber_subscriptions_tenant (tenant_id, current_period_end),
  KEY subscriber_subscriptions_subscriber (subscriber_id),
  CONSTRAINT fk_subscriber_subscriptions_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  CONSTRAINT fk_subscriber_subscriptions_subscriber FOREIGN KEY (subscriber_id) REFERENCES tenant_subscribers(id) ON DELETE CASCADE,
  CONSTRAINT fk_subscriber_subscriptions_plan FOREIGN KEY (service_plan_id) REFERENCES service_plans(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Traceability: which subscription generated this invoice (same pattern as
-- platform_invoices.subscription_id). Nullable — one-off/manual invoices
-- (vouchers, ad-hoc charges) aren't tied to a recurring subscription.
ALTER TABLE subscriber_invoices
  ADD COLUMN subscription_id bigint unsigned DEFAULT NULL AFTER subscriber_id,
  ADD CONSTRAINT fk_subscriber_invoices_subscription FOREIGN KEY (subscription_id) REFERENCES subscriber_subscriptions(id);

-- Superseded by subscriber_subscriptions -> service_plans above, same
-- reasoning as dropping tenants.billing_plan in 006_platform_billing.sql:
-- a single "current plan" pointer can't represent plan-change history or
-- billing/gateway state, which subscriber_subscriptions now owns. The FK
-- (fk_tenant_subscribers_plan, from 004_billing_seam.sql) must be dropped
-- in the same statement as its column.
ALTER TABLE tenant_subscribers
  DROP FOREIGN KEY fk_tenant_subscribers_plan,
  DROP COLUMN service_plan_id;
