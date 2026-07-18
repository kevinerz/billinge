#!/usr/bin/env bash
# Reloads FreeRADIUS so newly added/edited NAS entries (read_clients=yes
# loads from SQL at startup only, not per-packet) take effect, without
# dropping in-flight accounting sessions the way a full restart would.
# `systemctl reload` sends SIGHUP to the freeradius daemon — the supported way to reload
# config in place. Needs root — run with sudo if not already root.
set -euo pipefail

systemctl reload freeradius
echo "==> reloaded freeradius"
