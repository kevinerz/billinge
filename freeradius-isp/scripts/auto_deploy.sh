#!/usr/bin/env bash
# Dijalankan lewat cron secara berkala. Cek apakah ada commit baru di
# GitHub — kalau ada DAN yang berubah menyentuh freeradius-isp/, tarik lalu
# deploy ulang config + restart freeradius. Kalau tidak ada perubahan,
# keluar tanpa melakukan apa-apa (murah, aman dipanggil sesering apa pun).
#
# Setup cron (jalankan sebagai root, tiap 5 menit):
#   crontab -e
#   */5 * * * * /opt/billinge/freeradius-isp/scripts/auto_deploy.sh >> /var/log/freeradius-isp-autodeploy.log 2>&1
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"  # /opt/billinge
cd "$REPO_ROOT"

BEFORE="$(git rev-parse HEAD)"
git fetch origin main --quiet
AFTER="$(git rev-parse origin/main)"

if [ "$BEFORE" = "$AFTER" ]; then
	exit 0
fi

echo "[$(date -Iseconds)] update found: $BEFORE -> $AFTER"
git pull --quiet origin main

if git diff --name-only "$BEFORE" "$AFTER" | grep -q '^freeradius-isp/'; then
	echo "[$(date -Iseconds)] freeradius-isp changed, redeploying config"
	bash "$REPO_ROOT/freeradius-isp/scripts/deploy_config.sh"
	systemctl restart freeradius
	echo "[$(date -Iseconds)] freeradius restarted"
else
	echo "[$(date -Iseconds)] update was outside freeradius-isp/, nothing to redeploy here"
fi
