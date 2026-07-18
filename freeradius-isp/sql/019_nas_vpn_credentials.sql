-- Kredensial VPN dial-in per-NAS (untuk tenant yang konek lewat VPN Hub,
-- lihat docs/mikrotik-vpn-hub.md). SENGAJA tabel terpisah dari `nas`,
-- BUKAN kolom tambahan di `nas` — karena `nas` dibaca oleh akun MySQL
-- least-privilege RADIUS (RADIUS_DB_USER punya SELECT di nas untuk
-- read_clients). VPN password tidak boleh terbaca oleh proses RADIUS,
-- jadi disimpan di tabel ini yang TIDAK diberi grant apa pun ke
-- RADIUS_DB_USER (lihat scripts/provision_db_users.sh).
--
-- Satu baris per NAS: tiap Mikrotik tenant punya dial-in VPN sendiri
-- dengan IP tetap sendiri (remote_address = nas.nasname = 10.201.0.x).
-- nas_id int(10) (bukan unsigned) supaya cocok dengan tipe nas.id di
-- skema bawaan FreeRADIUS (sql/001).
CREATE TABLE nas_vpn_credentials (
  nas_id          int(10) NOT NULL PRIMARY KEY,
  vpn_username    varchar(64) NOT NULL UNIQUE,
  vpn_password    varchar(128) NOT NULL,
  remote_address  varchar(64) NOT NULL,
  created_at      timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_nas_vpn_nas FOREIGN KEY (nas_id) REFERENCES nas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
