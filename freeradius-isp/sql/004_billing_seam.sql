-- Forward-looking seam for a future billing layer. Deliberately minimal —
-- full billing (invoicing, payments, usage-based pricing) is out of scope for
-- this phase. Convention for all future billing tables: always a tenant_id
-- column, always an index on (tenant_id, created_at).

CREATE TABLE service_plans (
  id                  bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id           bigint unsigned NOT NULL,
  name                varchar(100) NOT NULL,
  price               decimal(12,2) NOT NULL DEFAULT 0,
  mikrotik_rate_limit varchar(64) DEFAULT NULL,
  -- Ties a plan to the radgroupreply groupname that carries its RADIUS reply
  -- attributes (e.g. Mikrotik-Rate-Limit) — assigning a subscriber to a plan
  -- is then just ensuring the matching radusergroup row exists.
  radius_groupname    varchar(64) NOT NULL,
  created_at          timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY service_plans_tenant_created (tenant_id, created_at),
  CONSTRAINT fk_service_plans_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tenant_subscribers (
  id               bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  tenant_id        bigint unsigned NOT NULL,
  username         varchar(64) NOT NULL,
  full_name        varchar(255) DEFAULT NULL,
  phone            varchar(32) DEFAULT NULL,
  address          varchar(255) DEFAULT NULL,
  service_plan_id  bigint unsigned DEFAULT NULL,
  status            enum('active','suspended','terminated') NOT NULL DEFAULT 'active',
  created_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY tenant_subscribers_tenant_created (tenant_id, created_at),
  KEY tenant_subscribers_tenant_username (tenant_id, username),
  CONSTRAINT fk_tenant_subscribers_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE,
  CONSTRAINT fk_tenant_subscribers_plan FOREIGN KEY (service_plan_id) REFERENCES service_plans(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
