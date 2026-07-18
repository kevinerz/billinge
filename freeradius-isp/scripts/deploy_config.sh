#!/usr/bin/env bash
# Deploys config/raddb/* over /etc/freeradius and wires .env into the
# systemd unit — the part of install_ubuntu.sh that's safe/fast to re-run
# often (no apt-get). Split out so scripts/auto_deploy.sh can redeploy on
# every git change without repeating the package-install step each time.
#
# Usage: sudo scripts/deploy_config.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
	echo "Run as root (sudo scripts/deploy_config.sh)" >&2
	exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FR_ETC=/etc/freeradius

if [ ! -f "$REPO_ROOT/.env" ]; then
	echo "No .env at $REPO_ROOT/.env — copy .env.example to .env and fill in real values first." >&2
	exit 1
fi

echo "==> deploying config/raddb over $FR_ETC"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/clients.conf" "$FR_ETC/clients.conf"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/dictionary.isp_tenant" "$FR_ETC/dictionary.isp_tenant"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/policy.d/isp_tenant" "$FR_ETC/policy.d/isp_tenant"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/policy.d/isp_voucher" "$FR_ETC/policy.d/isp_voucher"
install -o freerad -g freerad -m 0644 "$REPO_ROOT/config/raddb/policy.d/isp_subscriber" "$FR_ETC/policy.d/isp_subscriber"
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

echo "==> config deployed"
