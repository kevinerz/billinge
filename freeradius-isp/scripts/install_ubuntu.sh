#!/usr/bin/env bash
# Usage: sudo scripts/install_ubuntu.sh
#
# Installs FreeRADIUS 3.2.x directly on Ubuntu 24.04 (no Docker) and
# deploys this repo's config/raddb/* over the stock config. MySQL is
# assumed to be on a SEPARATE server — this script does not install or
# configure MySQL itself, only points FreeRADIUS at it via .env.
#
# Idempotent-ish: safe to re-run after editing config/raddb/* to redeploy,
# but always review `git diff` on /etc/freeradius before trusting a rerun
# blindly (this OVERWRITES clients.conf, sites-available/default,
# mods-available/sql, and the queries.conf/dictionary/policy files below).
#
# Order: run this FIRST (installs the FreeRADIUS package + deploys config),
# THEN scripts/bootstrap_db.sh (needs `mysql` client, which this installs),
# THEN scripts/provision_db_users.sh, then start onboarding tenants/NAS.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
	echo "Run as root (sudo scripts/install_ubuntu.sh)" >&2
	exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FR_ETC=/etc/freeradius

if [ ! -f "$REPO_ROOT/.env" ]; then
	echo "No .env at $REPO_ROOT/.env — copy .env.example to .env and fill in real values first." >&2
	exit 1
fi

echo "==> installing packages"
apt-get update
apt-get install -y freeradius freeradius-mysql freeradius-utils mysql-client openssl git

echo "==> deploying config/raddb over $FR_ETC"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/clients.conf" "$FR_ETC/clients.conf"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/dictionary.isp_tenant" "$FR_ETC/dictionary.isp_tenant"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/policy.d/isp_tenant" "$FR_ETC/policy.d/isp_tenant"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/policy.d/isp_voucher" "$FR_ETC/policy.d/isp_voucher"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/sites-enabled/default" "$FR_ETC/sites-available/default"
install -o freerad -g freerad -m 0640 "$REPO_ROOT/config/raddb/mods-enabled/sql" "$FR_ETC/mods-available/sql"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/mods-config/sql/main/mysql/queries.conf" \
	"$FR_ETC/mods-config/sql/main/mysql/queries.conf"

# sites-enabled/default is already a symlink to ../sites-available/default
# out of the box on Debian/Ubuntu packaging — nothing to do there.
# mods-enabled/sql is NOT enabled by default; symlink it if missing.
if [ ! -e "$FR_ETC/mods-enabled/sql" ]; then
	ln -s ../mods-available/sql "$FR_ETC/mods-enabled/sql"
	echo "==> enabled mods-enabled/sql"
fi

# Wire the local dictionary into the main one, once.
if ! grep -q 'dictionary.isp_tenant' "$FR_ETC/dictionary" 2>/dev/null; then
	echo '$INCLUDE dictionary.isp_tenant' >> "$FR_ETC/dictionary"
	echo "==> wired dictionary.isp_tenant into $FR_ETC/dictionary"
fi

echo "==> wiring .env into the freeradius systemd unit"
mkdir -p /etc/systemd/system/freeradius.service.d
cat > /etc/systemd/system/freeradius.service.d/override.conf <<EOF
[Service]
EnvironmentFile=$REPO_ROOT/.env
EOF
chmod 600 "$REPO_ROOT/.env"
systemctl daemon-reload
systemctl enable freeradius

# Deliberately NOT starting/verifying freeradius here yet: mods-available/sql
# connects as RADIUS_DB_USER, which doesn't exist in MySQL until
# scripts/provision_db_users.sh runs — and that in turn needs the schema
# from scripts/bootstrap_db.sh to exist first. Starting the freeradius
# service (or running `freeradius -XC`, which actually opens a real
# connection pool, unlike a Docker build step) before both of those would
# just fail on a missing MySQL user, not a real config problem.
#
# Note: on Debian/Ubuntu the daemon binary is `freeradius`, NOT `radiusd`
# (that name is used by some other distros/upstream builds) — commands
# below and everywhere else in this repo use the correct one.
echo "==> package installed, config deployed, service enabled (not started yet)"
echo "==> next: scripts/bootstrap_db.sh"
echo "==> then: scripts/provision_db_users.sh"
echo "==> then: systemctl restart freeradius && freeradius -XC"
