#!/usr/bin/env bash
# Usage: scripts/add_nas.sh <tenant_slug> <nas_ip> <shortname> [description]
# Example: scripts/add_nas.sh isp-maju 203.0.113.10 maju-mikrotik-1 "Kantor pusat"
#
# Generates a unique random shared secret per NAS — never reuse one
# platform-wide secret across tenants (a compromised customer-premises
# Mikrotik should only ever leak that one NAS's secret).
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -lt 3 ]; then
	echo "Usage: $0 <tenant_slug> <nas_ip> <shortname> [description]" >&2
	exit 1
fi
TENANT_SLUG="$1"
NAS_IP="$2"
SHORTNAME="$3"
DESCRIPTION="${4:-RADIUS Client}"
SECRET="$(openssl rand -base64 24)"

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

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
	-e "INSERT INTO nas (tenant_id, nasname, shortname, secret, description) \
	    SELECT id, '$(sql_escape "$NAS_IP")', '$(sql_escape "$SHORTNAME")', '$(sql_escape "$SECRET")', '$(sql_escape "$DESCRIPTION")' \
	    FROM tenants WHERE slug = '$(sql_escape "$TENANT_SLUG")';"

echo "==> NAS '$NAS_IP' registered for tenant '$TENANT_SLUG'"
echo "==> secret: $SECRET"
echo "==> read_clients=yes only loads NAS entries at startup — reload FreeRADIUS now:"
echo "    scripts/reload_freeradius.sh"
