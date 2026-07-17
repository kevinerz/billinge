CREATE TABLE tenants (
  id            bigint unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
  slug          varchar(64) NOT NULL UNIQUE,
  name          varchar(255) NOT NULL,
  status        enum('trial','active','suspended') NOT NULL DEFAULT 'trial',
  billing_plan  varchar(64) DEFAULT NULL,
  created_at    timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
