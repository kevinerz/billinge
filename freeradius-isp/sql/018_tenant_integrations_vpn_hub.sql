-- Adds 'vpn_hub' as a fourth integration_type, alongside
-- payment_gateway/whatsapp/sms/email from sql/017. Stores the credentials
-- for a tenant's dial-in to the Mikrotik VPN hub (see
-- docs/mikrotik-vpn-hub.md) the same way as every other integration: JSON
-- blob in `credentials` (here: {username, password, remote_address,
-- ipsec_psk}), scoped per-tenant, same zero-grant treatment as every other
-- row in this table for the RADIUS-core DB account
-- (scripts/provision_db_users.sh never touches tenant_integrations at all).
ALTER TABLE tenant_integrations
  MODIFY COLUMN integration_type enum('payment_gateway','whatsapp','sms','email','vpn_hub') NOT NULL;
