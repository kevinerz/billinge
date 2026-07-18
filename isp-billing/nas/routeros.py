"""Client RouterOS API buat CHR gateway (103.139.163.150:7652, API-SSL).

Dipakai oleh nas/views.py: saat NAS baru dibuat dengan opsi "konek lewat
VPN Hub", backend connect ke CHR dan menambahkan satu PPP secret dengan
remote-address tetap (= nasname / IP tenant di 10.201.0.0/24). Dengan
begitu tidak perlu lagi copas script manual ke CHR — lihat
freeradius-isp/docs/mikrotik-vpn-hub.md.

Semua kegagalan (CHR tidak reachable, kredensial API salah, dll) diangkat
sebagai RouterOsError supaya view bisa menanganinya dengan rapi (rollback
NAS, kembalikan pesan yang jelas ke dashboard)."""
import ssl

from django.conf import settings


class RouterOsError(Exception):
    pass


def _connect():
    if not settings.ROUTEROS_USER:
        raise RouterOsError(
            'ROUTEROS_USER belum diset di .env — provisioning VPN otomatis dimatikan. '
            'Isi ROUTEROS_* di .env atau daftarkan PPP secret manual di CHR.'
        )
    try:
        from librouteros import connect
    except ImportError as e:  # pragma: no cover
        raise RouterOsError(f'library librouteros belum terpasang (pip install -r requirements.txt): {e}')

    kwargs = dict(
        host=settings.ROUTEROS_HOST,
        port=settings.ROUTEROS_API_PORT,
        username=settings.ROUTEROS_USER,
        password=settings.ROUTEROS_PASSWORD,
        timeout=10,
    )
    if settings.ROUTEROS_USE_TLS:
        ctx = ssl.create_default_context()
        if not settings.ROUTEROS_TLS_VERIFY:
            # CHR default pakai cert self-signed di API-SSL — tanpa ini
            # handshake gagal. Aman-ish karena target-nya IP tetap milik
            # sendiri; nyalakan verifikasi begitu CHR punya cert tervalidasi.
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        # RouterOS lama kadang menegosiasi cipher yang ditolak SECLEVEL
        # default OpenSSL modern — longgarkan supaya handshake jalan.
        try:
            ctx.set_ciphers('DEFAULT:@SECLEVEL=0')
        except ssl.SSLError:
            pass
        kwargs['ssl_wrapper'] = ctx.wrap_socket

    try:
        return connect(**kwargs)
    except Exception as e:
        raise RouterOsError(
            f'Gagal konek ke RouterOS API {settings.ROUTEROS_HOST}:{settings.ROUTEROS_API_PORT} — {e}'
        )


def add_vpn_secret(username, password, remote_address, comment=''):
    """Tambah/timpa satu PPP secret di CHR. Idempoten: kalau username sudah
    ada (mis. re-provision), yang lama dihapus dulu."""
    api = _connect()
    try:
        path = api.path('ppp', 'secret')
        stale_ids = [row['.id'] for row in path if row.get('name') == username]
        for sid in stale_ids:
            path.remove(sid)
        path.add(
            name=username,
            password=password,
            profile=settings.VPN_PROFILE,
            service='any',
            comment=comment,
            **{'remote-address': remote_address},
        )
    except RouterOsError:
        raise
    except Exception as e:
        raise RouterOsError(f'Gagal menambah PPP secret di CHR: {e}')
    finally:
        _safe_close(api)


def remove_vpn_secret(username):
    """Hapus PPP secret tenant (dipanggil saat NAS dihapus). Dibuat toleran:
    kalau CHR sedang tidak reachable, jangan sampai gagal-total menghapus
    NAS — caller boleh menelan RouterOsError-nya."""
    api = _connect()
    try:
        path = api.path('ppp', 'secret')
        ids = [row['.id'] for row in path if row.get('name') == username]
        for sid in ids:
            path.remove(sid)
    except RouterOsError:
        raise
    except Exception as e:
        raise RouterOsError(f'Gagal menghapus PPP secret di CHR: {e}')
    finally:
        _safe_close(api)


def _safe_close(api):
    try:
        api.close()
    except Exception:
        pass
