#!/usr/bin/env bash
# Usage: scripts/provision_db_users.sh
#
# Creates a LEAST-PRIVILEGE MySQL user for FreeRADIUS itself
# (RADIUS_DB_USER/RADIUS_DB_PASSWORD in .env), separate from the
# general-purpose MYSQL_USER that scripts/bootstrap_db.sh and every other
# scripts/*.sh CLI tool (and any future dashboard/API) uses.
#
# Why: FreeRADIUS only ever needs to touch RADIUS-core tables — it has no
# business reading platform_payments, subscriber_payments, users
# (password hashes!), audit_logs, or any other billing/admin table. If the
# FreeRADIUS process or its config were ever compromised, a shared
# full-access credential would hand an attacker the entire billing/user
# database along with it. Grants below are scoped to exactly the tables and
# operations config/raddb/mods-config/sql/main/mysql/queries.conf and
# policy.d/{isp_tenant,isp_voucher} actually use — nothing more.
#
# Run this once after scripts/bootstrap_db.sh (needs the tables to exist)
# and again after adding any migration that changes what FreeRADIUS itself
# reads/writes. Requires MYSQL_ADMIN_USER/MYSQL_ROOT_PASSWORD — that admin
# account is only ever used here, never by the running application.
#
# Grants are scoped to RADIUS_VM_IP specifically, not '%' (any host) — with
# MySQL on a separate server reachable over a real network, '%' would let
# this account authenticate from anywhere that has the password, not just
# this FreeRADIUS VM.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a
[ -f .env ] && source .env
set +a

MYSQL_HOST="${MYSQL_HOST:?MYSQL_HOST must be set (copy .env.example to .env)}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-radius}"
MYSQL_ADMIN_USER="${MYSQL_ADMIN_USER:-root}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD must be set (copy .env.example to .env)}"
RADIUS_DB_USER="${RADIUS_DB_USER:?RADIUS_DB_USER must be set (copy .env.example to .env)}"
RADIUS_DB_PASSWORD="${RADIUS_DB_PASSWORD:?RADIUS_DB_PASSWORD must be set (copy .env.example to .env)}"
RADIUS_VM_IP="${RADIUS_VM_IP:?RADIUS_VM_IP must be set (copy .env.example to .env) — the IP of this VM as seen by the MySQL server}"

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_ADMIN_USER" -p"$MYSQL_ROOT_PASSWORD" -e "
	CREATE USER IF NOT EXISTS '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}' IDENTIFIED BY '${RADIUS_DB_PASSWORD}';
	ALTER USER '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}' IDENTIFIED BY '${RADIUS_DB_PASSWORD}';

	-- authorize: read-only lookups
	GRANT SELECT ON ${MYSQL_DATABASE}.radcheck      TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';
	GRANT SELECT ON ${MYSQL_DATABASE}.radreply      TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';
	GRANT SELECT ON ${MYSQL_DATABASE}.radgroupcheck TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';
	GRANT SELECT ON ${MYSQL_DATABASE}.radgroupreply TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';
	GRANT SELECT ON ${MYSQL_DATABASE}.radusergroup  TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- accounting: inserts new sessions, updates on interim/stop/reboot, and
	-- reads its own rows for Simultaneous-Use checks
	GRANT SELECT, INSERT, UPDATE ON ${MYSQL_DATABASE}.radacct TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- post-auth: append-only login log, never read back by FreeRADIUS itself
	GRANT INSERT ON ${MYSQL_DATABASE}.radpostauth TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- NAS lookup (read_clients) + last_contact_at liveness update
	GRANT SELECT, UPDATE ON ${MYSQL_DATABASE}.nas TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- tenant status check (isp_tenant_check_active) — read-only, FreeRADIUS
	-- never creates/edits/deletes a tenant
	GRANT SELECT ON ${MYSQL_DATABASE}.tenants TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- voucher redemption marking (isp_voucher_mark_redeemed)
	GRANT SELECT, UPDATE ON ${MYSQL_DATABASE}.vouchers TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- Subscriber-suspend check (isp_subscriber_check_active) needs to read
	-- ONLY tenant_subscribers.status (+ .id, referenced in the JOIN's ON
	-- clause — MySQL column-level grants require every column touched
	-- anywhere in the query, not just the SELECT list). Column-level, not
	-- table-level: this is the one narrow exception to the RADIUS process
	-- otherwise never touching tenant_subscribers at all (see below), and
	-- it is deliberately scoped so the RADIUS process still can never read
	-- a subscriber's KTP, email, phone, address, or GPS pin.
	GRANT SELECT (id, status) ON ${MYSQL_DATABASE}.tenant_subscribers TO '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}';

	-- Everything else (platform_*, users, password_resets, audit_logs,
	-- notifications, tenant_billing_profiles, service_plans,
	-- voucher_batches, tenant_integrations, and every OTHER column of
	-- tenant_subscribers besides id/status above) gets NO grant at all —
	-- not even SELECT. tenant_integrations' live API keys/tokens and every
	-- subscriber PII field stay completely out of the RADIUS process's reach.

	FLUSH PRIVILEGES;"

echo "==> '${RADIUS_DB_USER}'@'${RADIUS_VM_IP}' provisioned with RADIUS-core-only access to ${MYSQL_DATABASE}"
echo "==> now start freeradius for real and verify config (this actually connects to MySQL):"
echo "    systemctl restart freeradius && freeradius -XC"
