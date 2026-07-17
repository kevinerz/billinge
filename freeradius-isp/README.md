# freeradius-isp

Project terpisah untuk setup FreeRADIUS 3.2.x — tidak digabung dengan project ERP-NEXT1.

## Struktur

- `config/` — file konfigurasi FreeRADIUS (raddb: clients.conf, mods-enabled, sites-enabled, dll.)
- `sql/` — schema/migrasi database radacct (untuk billing/accounting)
- `scripts/` — script setup/deploy
- `docs/` — catatan integrasi (Mikrotik, hotspot, PPPoE, dll.)

## Status

Skema database (`sql/001`-`017`, ~30 tabel) dan konfigurasi FreeRADIUS multi-tenant sudah selesai dirancang — lihat `docs/architecture.md`. Aplikasi (dashboard/API) belum dibangun.

## Deployment

Install langsung di Ubuntu 24.04 VM (bukan Docker) — MySQL di server terpisah. Urutan setup: `scripts/install_ubuntu.sh` → `scripts/bootstrap_db.sh` → `scripts/provision_db_users.sh` → `systemctl restart freeradius && freeradius -XC` (di Debian/Ubuntu binary-nya bernama `freeradius`, bukan `radiusd`). Detail lengkap di `docs/architecture.md`.

Stack aplikasi yang direncanakan (belum dikerjakan): Django + Django REST Framework (backend), React + Vite + TypeScript (frontend).
