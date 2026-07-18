#!/usr/bin/env bash
# Usage: scripts/add_tenant.sh <slug> <name>
# Example: scripts/add_tenant.sh isp-maju "ISP Maju Jaya"
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -lt 2 ]; then
	echo "Usage: $0 <slug> <name>" >&2
	exit 1
fi
SLUG="$1"
NAME="$2"

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
	-e "INSERT INTO tenants (slug, name, status) VALUES ('$(sql_escape "$SLUG")', '$(sql_escape "$NAME")', 'active');"

echo "==> tenant '$SLUG' created"
