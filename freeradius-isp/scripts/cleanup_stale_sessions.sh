#!/usr/bin/env bash
# Usage: scripts/cleanup_stale_sessions.sh [stale_minutes]
#
# Closes radacct rows left open by a Mikrotik that went down without ever
# telling FreeRADIUS — a plain network blip or power loss sends nothing;
# there's no Accounting-Off, no final Interim-Update, nothing. RouterOS is
# also not reliable about sending Accounting-On when it comes back up
# either, so don't assume that query (mods-config/sql/main/mysql/
# queries.conf's `accounting-on` type) will ever fire and clean these up
# for you — it's a bonus if it does, not the actual fix.
#
# Left alone, these "zombie" sessions (acctstoptime IS NULL forever):
#   - poison Simultaneous-Use checks (a subscriber capped at 1 concurrent
#     session looks permanently "still connected" and can't log back in)
#   - make "who's online now" queries/dashboards lie
#
# Default threshold (15 min) assumes the common Mikrotik
# interim-update=5m setting from docs/mikrotik-pppoe-integration.md — 3x
# the interval before calling a session stale. Pass a different value if
# your interim-update interval differs.
#
# Run this on a schedule — it's a sweep, not a one-time fix. On this
# Ubuntu VM, the simplest option is a root crontab entry, e.g. every 5 min:
#   */5 * * * * /opt/freeradius-isp/scripts/cleanup_stale_sessions.sh >> /var/log/freeradius-isp-cleanup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")/.."

STALE_MINUTES="${1:-15}"
if ! [[ "$STALE_MINUTES" =~ ^[0-9]+$ ]]; then
	echo "stale_minutes must be a positive integer, got: $STALE_MINUTES" >&2
	exit 1
fi

set -a
[ -f .env ] && source .env
set +a

MYSQL_HOST="${MYSQL_HOST:?MYSQL_HOST must be set (copy .env.example to .env)}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-radius}"
MYSQL_USER="${MYSQL_USER:-radius}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD must be set (copy .env.example to .env)}"

mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "
	UPDATE radacct
	SET acctstoptime = NOW(),
	    acctsessiontime = TIMESTAMPDIFF(SECOND, acctstarttime, NOW()),
	    acctterminatecause = 'Stale-Session-Cleanup'
	WHERE acctstoptime IS NULL
	  AND COALESCE(acctupdatetime, acctstarttime) < NOW() - INTERVAL ${STALE_MINUTES} MINUTE;
	SELECT ROW_COUNT() AS sessions_closed;"
