#!/usr/bin/env bash
# Dijalankan lewat cron secara berkala. Cek apakah ada commit baru di
# GitHub — kalau ada DAN yang berubah menyentuh isp-billing/, tarik, install
# ulang dependency Python kalau requirements.txt berubah, jalankan migrate,
# lalu restart proses Django. Kalau tidak ada perubahan, keluar tanpa
# melakukan apa-apa.
#
# CATATAN: script ini cuma jalankan `migrate` (menerapkan migrasi yang SUDAH
# ada di repo), BUKAN `makemigrations`. Kalau nambah app/model BARU,
# `makemigrations` harus dijalankan manual sekali di VM ini, lalu file
# migrasinya di-commit+push balik ke GitHub — supaya jadi bagian resmi repo,
# bukan cuma ada di VM ini doang.
#
# Setup cron (tiap 5 menit):
#   crontab -e
#   */5 * * * * /opt/billinge/isp-billing/scripts/auto_deploy.sh >> /var/log/isp-billing-autodeploy.log 2>&1
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"  # /opt/billinge
APP_DIR="$REPO_ROOT/isp-billing"
cd "$REPO_ROOT"

BEFORE="$(git rev-parse HEAD)"
git fetch origin main --quiet
AFTER="$(git rev-parse origin/main)"

if [ "$BEFORE" = "$AFTER" ]; then
	exit 0
fi

echo "[$(date -Iseconds)] update found: $BEFORE -> $AFTER"
CHANGED="$(git diff --name-only "$BEFORE" "$AFTER")"
git pull --quiet origin main

if ! echo "$CHANGED" | grep -q '^isp-billing/'; then
	echo "[$(date -Iseconds)] update was outside isp-billing/, nothing to redeploy here"
	exit 0
fi

echo "[$(date -Iseconds)] isp-billing changed, redeploying"
cd "$APP_DIR"
source venv/bin/activate

if echo "$CHANGED" | grep -q '^isp-billing/requirements.txt'; then
	echo "[$(date -Iseconds)] requirements.txt changed, reinstalling packages"
	pip install -r requirements.txt --quiet
fi

python manage.py migrate --noinput

pkill -f "manage.py runserver" || true
sleep 1
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &
echo "[$(date -Iseconds)] django restarted"
