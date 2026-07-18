#!/usr/bin/env bash
# Usage: sudo scripts/install_ubuntu.sh
#
# Installs FreeRADIUS 3.2.x directly on Ubuntu 24.04 (no Docker) and
# deploys this repo's config/raddb/* over the stock config. MySQL is
# assumed to be on a SEPARATE server — this script does not install or
# configure MySQL itself, only points FreeRADIUS at it via .env.
#
# This installs PACKAGES (apt) then hands off to scripts/deploy_config.sh
# for the actual config deployment — that part is split out so
# scripts/auto_deploy.sh can redeploy config on every git change without
# repeating the (slow, network-heavy) package-install step each time.
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

if [ ! -f "$REPO_ROOT/.env" ]; then
	echo "No .env at $REPO_ROOT/.env — copy .env.example to .env and fill in real values first." >&2
	exit 1
fi

echo "==> installing packages"
apt-get update
apt-get install -y freeradius freeradius-mysql freeradius-utils mysql-client openssl git

bash "$REPO_ROOT/scripts/deploy_config.sh"

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
