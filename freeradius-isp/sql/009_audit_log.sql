-- Generic audit trail for future dashboard/API actions (tenant onboarding,
-- NAS changes, invoice/payment status changes, etc). tenant_id NULL means a
-- platform-level action (e.g. a super_admin created a new tenant); user_id
-- NULL means a script/system action rather than a logged-in user.
CREATE TABLE audit_logs (
  id           bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id    bigint unsigned DEFAULT NULL,
  user_id      bigint unsigned DEFAULT NULL,
  action       varchar(100) NOT NULL, -- e.g. 'tenant.created', 'nas.added', 'invoice.paid'
  entity_type  varchar(64) DEFAULT NULL,
  entity_id    bigint unsigned DEFAULT NULL,
  metadata     json DEFAULT NULL,
  created_at   timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY audit_logs_tenant_created (tenant_id, created_at),
  KEY audit_logs_user_created (user_id, created_at),
  CONSTRAINT fk_audit_logs_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE SET NULL,
  CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
