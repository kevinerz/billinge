-- Dashboard/API user accounts (not built yet — schema only, for when that
-- layer is built). Three roles:
--   super_admin  -> platform operator, tenant_id NULL, sees/manages all tenants
--   tenant_admin -> full access within exactly one tenant
--   tenant_staff -> restricted access within exactly one tenant (e.g. CS: can
--                   view/add subscribers, cannot touch billing/NAS)
-- The staff/admin permission split itself (what tenant_staff can and can't
-- do) is an application-layer concern, not encoded in this table.
--
-- password_hash must hold a proper hash (bcrypt/argon2) — this is unrelated
-- to radcheck.Cleartext-Password, which is a RADIUS protocol requirement
-- (see docs/mikrotik-pppoe-integration.md), not a precedent for how
-- dashboard credentials should be stored.
CREATE TABLE users (
  id             bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id      bigint unsigned DEFAULT NULL, -- NULL only for super_admin
  role           enum('super_admin','tenant_admin','tenant_staff') NOT NULL,
  email          varchar(255) NOT NULL UNIQUE,
  password_hash  varchar(255) NOT NULL,
  full_name      varchar(255) DEFAULT NULL,
  status         enum('active','suspended') NOT NULL DEFAULT 'active',
  last_login_at  timestamp NULL DEFAULT NULL,
  created_at     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY users_tenant (tenant_id),
  CONSTRAINT fk_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  CONSTRAINT chk_users_role_tenant CHECK (
    (role = 'super_admin' AND tenant_id IS NULL) OR
    (role IN ('tenant_admin', 'tenant_staff') AND tenant_id IS NOT NULL)
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
