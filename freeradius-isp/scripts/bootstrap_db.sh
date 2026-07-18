#!/usr/bin/env bash
# Applies every migration in sql/ (in order) against the remote MySQL
# server (MYSQL_HOST — a separate machine, not this Ubuntu VM). Safe to
# re-run on an already-bootstrapped dev DB only in the sense that MySQL
# will error on "table already exists" — this is meant for a fresh
# database, not idempotent migrations.
#
# Run scripts/provision_db_users.sh AFTER this — GRANTing on a specific
# table requires the table to already exist.
set -euo pipefail
cd "$(dirname "$0")/.."

set -a
[ -f .env ] && source .env
set +a

MYSQL_HOST="${MYSQL_HOST:?MYSQL_HOST must be set (copy .env.example to .env)}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_DATABASE="${MYSQL_DATABASE:-radius}"
MYSQL_USER="${MYSQL_USER:-radius}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:?MYSQL_PASSWORD must be set (copy .env.example to .env)}"

for f in sql/*.sql; do
	echo "==> applying $f"
	mysql -h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$f"
done

echo "==> done"
