-- Supports scripts/cleanup_stale_sessions.sh: finding "sessions still marked
-- open but not updated in a long time" needs to scan by (acctstoptime,
-- acctupdatetime) across ALL tenants, which none of radacct's existing
-- indexes (keyed off username or tenant_id first) serve well.
ALTER TABLE radacct
  ADD INDEX radacct_open_sessions (acctstoptime, acctupdatetime);
