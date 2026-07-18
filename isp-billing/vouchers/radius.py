"""Insert/hapus kredensial RADIUS mentah (radcheck/radusergroup) buat
voucher. Pakai raw SQL via connection.cursor(), BUKAN Django ORM — tabel
radusergroup memang tidak punya primary key sama sekali di schema aslinya
(lihat sql/001_freeradius_base_schema.sql), jadi tidak bisa dimodelkan
sebagai Django Model (ORM mewajibkan PK). radcheck sebenarnya punya PK
`id`, tapi dipakai raw SQL juga di sini biar konsisten satu gaya dengan
radusergroup dalam transaksi yang sama."""
import secrets

from django.db import connection

from .models import Voucher

VOUCHER_CODE_LENGTH_BYTES = 3  # -> 6 karakter hex


def generate_voucher_code():
    return secrets.token_hex(VOUCHER_CODE_LENGTH_BYTES).upper()


def unique_voucher_username(tenant_id, reserved=(), max_attempts=10):
    """reserved = username yang baru saja dipakai di batch yang sama dalam
    request ini (belum ke-commit ke DB, jadi belum kelihatan oleh query)."""
    for _ in range(max_attempts):
        code = generate_voucher_code()
        if code in reserved:
            continue
        if not Voucher.objects.filter(tenant_id=tenant_id, username=code).exists():
            return code
    raise RuntimeError(f'Gagal generate username voucher unik setelah {max_attempts} percobaan.')


def insert_radius_credential(cursor, tenant_id, username, password, groupname=None):
    cursor.execute(
        "INSERT INTO radcheck (tenant_id, username, attribute, op, value) VALUES (%s, %s, 'Cleartext-Password', ':=', %s)",
        [tenant_id, username, password],
    )
    if groupname:
        cursor.execute(
            "INSERT INTO radusergroup (username, groupname, priority, tenant_id) VALUES (%s, %s, 1, %s)",
            [username, groupname, tenant_id],
        )


def delete_radius_credentials(tenant_id, usernames):
    usernames = list(usernames)
    if not usernames:
        return
    placeholders = ','.join(['%s'] * len(usernames))
    with connection.cursor() as cursor:
        cursor.execute(
            f"DELETE FROM radcheck WHERE tenant_id = %s AND username IN ({placeholders})",
            [tenant_id, *usernames],
        )
        cursor.execute(
            f"DELETE FROM radusergroup WHERE tenant_id = %s AND username IN ({placeholders})",
            [tenant_id, *usernames],
        )
