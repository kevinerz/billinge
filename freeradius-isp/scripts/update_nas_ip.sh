#!/usr/bin/env bash
# Usage: scripts/update_nas_ip.sh <tenant_slug> <shortname> <new_ip>
# Example: scripts/update_nas_ip.sh isp-maju maju-mikrotik-1 203.0.113.55
#
# A Mikrotik reconnecting with a DIFFERENT ip than it registered with (ISP
# reassigned a dynamic WAN IP, or it moved to a new VPN tunnel address —
# see docs/architecture.md's CGNAT note) goes from "this tenant's router"
# to "Unrecognized NAS" the instant its old IP no longer matches
# nas.nasname — tenant resolution is entirely IP-based, so this is a full
# outage for every subscriber on that router until nasname is corrected.
#
# Identifies the NAS by `shortname` (stable, operator-assigned) rather than
# its old IP (which the operator may not remember exactly, and which is
# the very thing that just changed).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -lt 3 ]; then
	echo "Usage: $0 <tenant_slug> <shortname> <new_ip>" >&2
	exit 1
fi
TENANT_SLUG="$1"
SHORTNAME="$2"
NEW_IP="$3"

set -a
[ -f .env ] && source .env
set +a

MYSQL_HOST="${MYSQL_HOST:?MYSQL_HOST must be set (copy .env.example to .env)}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-radius}"
MYSQL_USER="${MYSQL_USER:-radius}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD must be set (copy .env.example to .env)}"

# Escape backslash BEFORE quote — escaping quote alone leaves a trailing
# backslash free to swallow the closing quote it should have protected.
sql_escape() { local s="${1//\\/\\\\}"; printf '%s' "${s//\'/\\\'}"; }

RESULT="$(mysql -N -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
	UPDATE nas n
	JOIN tenants t ON t.id = n.tenant_id
	SET n.nasname = '$(sql_escape "$NEW_IP")'
	WHERE t.slug = '$(sql_escape "$TENANT_SLUG")' AND n.shortname = '$(sql_escape "$SHORTNAME")';
	SELECT ROW_COUNT();")"

if [ "$RESULT" = "0" ]; then
	echo "No NAS found for tenant '$TENANT_SLUG' with shortname '$SHORTNAME'" >&2
	exit 1
fi

echo "==> NAS '$SHORTNAME' (tenant '$TENANT_SLUG') updated to $NEW_IP"
echo "==> read_clients=yes only loads NAS entries at startup — reload FreeRADIUS now:"
echo "    scripts/reload_freeradius.sh"
