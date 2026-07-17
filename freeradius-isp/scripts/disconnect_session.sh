#!/usr/bin/env bash
# Usage: scripts/disconnect_session.sh <tenant_slug> <username>
#
# Sends a RADIUS Disconnect-Request (RFC 5176) to force an already-connected
# subscriber offline right now, instead of waiting for their session to end
# on its own. RADIUS accounting alone only records sessions — it cannot end
# one — so this is the missing enforcement piece for suspending a
# subscriber (quota used up, non-payment) in real time rather than just
# blocking their NEXT login attempt.
#
# Requires the Mikrotik to accept CoA/Disconnect packets:
#   /radius incoming accept=yes
#   /radius incoming port=3799   (RouterOS default, matches radclient below)
#
# This is a manual/scriptable capability only — nothing calls this
# automatically yet. Wiring it to "quota exhausted" or "invoice overdue"
# is future billing-engine/app-layer work (see docs/architecture.md).
#
# Looks up the subscriber's most recent OPEN session (acctstoptime IS NULL)
# to get the NAS IP + session id, then resolves that NAS's secret — and
# checks the NAS actually belongs to the given tenant, so one tenant can
# never disconnect another tenant's session even by an operator typo.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ $# -lt 2 ]; then
	echo "Usage: $0 <tenant_slug> <username>" >&2
	exit 1
fi
TENANT_SLUG="$1"
USERNAME="$2"

set -a
[ -f .env ] && source .env
set +a

MYSQL_HOST="${MYSQL_HOST:?MYSQL_HOST must be set (copy .env.example to .env)}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-radius}"
MYSQL_USER="${MYSQL_USER:-radius}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD must be set (copy .env.example to .env)}"

query() {
	mysql -N -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "$1"
}

# Escape backslash BEFORE quote — escaping quote alone leaves a trailing
# backslash free to swallow the closing quote it should have protected.
sql_escape() { local s="${1//\\/\\\\}"; printf '%s' "${s//\'/\\\'}"; }

SESSION_ROW="$(query "
	SELECT a.acctsessionid, a.nasipaddress
	FROM radacct a
	JOIN tenants t ON t.id = a.tenant_id
	WHERE t.slug = '$(sql_escape "$TENANT_SLUG")'
	  AND a.username = '$(sql_escape "$USERNAME")'
	  AND a.acctstoptime IS NULL
	ORDER BY a.acctstarttime DESC
	LIMIT 1")"

if [ -z "$SESSION_ROW" ]; then
	echo "No open session found for '$USERNAME' under tenant '$TENANT_SLUG'" >&2
	exit 1
fi
IFS=$'\t' read -r ACCTSESSIONID NASIP <<< "$SESSION_ROW"

SECRET="$(query "
	SELECT n.secret
	FROM nas n
	JOIN tenants t ON t.id = n.tenant_id
	WHERE n.nasname = '$(sql_escape "$NASIP")' AND t.slug = '$(sql_escape "$TENANT_SLUG")'")"

if [ -z "$SECRET" ]; then
	echo "NAS $NASIP is not registered to tenant '$TENANT_SLUG' — refusing to disconnect" >&2
	exit 1
fi

echo "==> disconnecting '$USERNAME' (session $ACCTSESSIONID) via NAS $NASIP"
printf 'User-Name = "%s"\nAcct-Session-Id = "%s"\n' "$USERNAME" "$ACCTSESSIONID" | \
	radclient -x "${NASIP}:3799" disconnect "$SECRET"
