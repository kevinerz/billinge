-- Core multi-tenant migration. Adds tenant_id to every rlm_sql table so every
-- query becomes "WHERE username = ? AND tenant_id = ?", closing the
-- global-username-collision hole in the stock FreeRADIUS schema.
--
-- Tenant is resolved once per request from the matched NAS's Client-IP
-- (see config/raddb/policy.d/isp_tenant) and threaded into every query in
-- config/raddb/mods-config/sql/main/mysql/queries.conf.
--
-- Safe to run against empty tables only (fresh install) — adding a NOT NULL
-- column with no default to a populated table would fail.

ALTER TABLE radcheck
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX radcheck_tenant_username (tenant_id, username),
  ADD CONSTRAINT fk_radcheck_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE radreply
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX radreply_tenant_username (tenant_id, username),
  ADD CONSTRAINT fk_radreply_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE radgroupcheck
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX radgroupcheck_tenant_group (tenant_id, groupname),
  ADD CONSTRAINT fk_radgroupcheck_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE radgroupreply
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX radgroupreply_tenant_group (tenant_id, groupname),
  ADD CONSTRAINT fk_radgroupreply_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE radusergroup
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER username,
  ADD INDEX radusergroup_tenant_username (tenant_id, username),
  ADD CONSTRAINT fk_radusergroup_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;

ALTER TABLE radacct
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER radacctid,
  ADD INDEX radacct_tenant_username (tenant_id, username, acctstarttime),
  -- No CASCADE here: accounting rows are an audit trail and must outlive a
  -- deleted tenant. Deleting a tenant that still has radacct rows will be
  -- rejected until those rows are archived/purged deliberately.
  ADD CONSTRAINT fk_radacct_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE radpostauth
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX radpostauth_tenant_username (tenant_id, username, authdate),
  ADD CONSTRAINT fk_radpostauth_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id);

ALTER TABLE nas
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX nas_tenant (tenant_id),
  ADD CONSTRAINT fk_nas_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
  -- nasname stays globally UNIQUE (from 001) — this enforces the "one NAS IP
  -- maps to exactly one tenant" invariant the whole tenant-resolution design
  -- relies on (see docs/architecture.md).

ALTER TABLE radippool
  ADD COLUMN tenant_id bigint unsigned NOT NULL AFTER id,
  ADD INDEX radippool_tenant_pool (tenant_id, pool_name);
