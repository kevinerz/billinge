-- Three small, clearly-justified additions on top of the already-complete
-- structural schema — not new features, just companions to what exists:
--   1. nas.last_contact_at    -> is this router even online?
--   2. password_resets        -> users (007) needs a forgot-password flow
--   3. notifications          -> log of reminders/alerts actually sent

-- Updated on every RADIUS request that resolves a tenant (see
-- policy.d/isp_tenant's isp_tenant_resolve) — authorize, accounting, and
-- post-auth all touch it, so this stays fresh as long as the NAS is
-- actually talking to the server at all, not just when subscribers log in.
ALTER TABLE nas
  ADD COLUMN last_contact_at timestamp NULL DEFAULT NULL AFTER description;

-- Stores a hash of the reset token, never the token itself — same
-- principle as password_hash in users (007_users_roles.sql).
CREATE TABLE password_resets (
  id          bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id     bigint unsigned NOT NULL,
  token_hash  varchar(255) NOT NULL,
  expires_at  timestamp NOT NULL,
  used_at     timestamp NULL DEFAULT NULL,
  created_at  timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY password_resets_user (user_id),
  UNIQUE KEY password_resets_token_hash (token_hash),
  CONSTRAINT fk_password_resets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Log of every reminder/alert actually sent (invoice due, payment
-- confirmed, tenant suspended, etc) — lets a future billing engine check
-- "did I already send this?" before sending again, and gives an audit
-- trail independent of whatever email/SMS/WhatsApp provider is used.
--
-- recipient_id / related_id are intentionally polymorphic (no FK): a
-- recipient is either a dashboard `users` row or a `tenant_subscribers`
-- row depending on recipient_type, and `related_*` points at whichever
-- invoice table triggered the notification. MySQL can't FK against "one of
-- two tables" cleanly, so this is enforced by the application, not the
-- schema. No uniqueness constraint on (category, related_id) either —
-- legitimate reminder cadences (day 1, day 3, day 7) send the same
-- category for the same invoice more than once by design.
CREATE TABLE notifications (
  id             bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id      bigint unsigned DEFAULT NULL, -- NULL = platform-level notification
  recipient_type enum('user','tenant_subscriber') NOT NULL,
  recipient_id   bigint unsigned NOT NULL,
  channel        enum('email','sms','whatsapp') NOT NULL,
  category       varchar(64) NOT NULL, -- e.g. 'invoice_reminder', 'payment_confirmed', 'tenant_suspended'
  related_type   varchar(64) DEFAULT NULL, -- e.g. 'platform_invoices', 'subscriber_invoices'
  related_id     bigint unsigned DEFAULT NULL,
  status         enum('queued','sent','failed') NOT NULL DEFAULT 'queued',
  error_message  varchar(255) DEFAULT NULL,
  sent_at        timestamp NULL DEFAULT NULL,
  created_at     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY notifications_tenant_created (tenant_id, created_at),
  KEY notifications_recipient (recipient_type, recipient_id),
  KEY notifications_related (related_type, related_id),
  CONSTRAINT fk_notifications_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
