#!/usr/bin/env bash
# Installs systemd units for Django, the Vite frontend, and Celery
# worker+beat, so all four survive a VM reboot automatically -- until now
# they only ran via manual `nohup ... &`, which dies on every restart
# (unlike nginx/redis-server, which already have their own systemd units
# from their apt packages).
#
# Usage: sudo scripts/install_systemd_services.sh
#
# NOTE: runs everything as root, same posture as the manual nohup setup
# it replaces -- not a production hardening step, just parity with what
# was already running. Tighten this (dedicated non-root user, gunicorn
# instead of `runserver`, etc.) before this VM is treated as production.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
	echo "Run as root (sudo scripts/install_systemd_services.sh)" >&2
	exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
UNITS="billinge-django billinge-frontend billinge-celery-worker billinge-celery-beat"

echo "==> stopping any manually-started (nohup) processes first"
pkill -f "manage.py runserver" || true
pkill -f "vite --host" || true
pkill -f "celery -A config worker" || true
pkill -f "celery -A config beat" || true
sleep 1

for unit in $UNITS; do
	install -m 0644 "$SCRIPT_DIR/systemd/$unit.service" "/etc/systemd/system/$unit.service"
done

systemctl daemon-reload
for unit in $UNITS; do
	systemctl enable --now "$unit"
done

echo "==> installed and started: $UNITS"
echo "==> check with: systemctl status $UNITS"
