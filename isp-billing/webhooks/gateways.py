"""Verifikasi signature & normalisasi status per payment gateway.

Setiap gateway punya cara verifikasi & nama field yang beda — modul ini
mengisolasi perbedaan itu supaya views.py tidak perlu tahu detail
Midtrans vs Xendit. Tambah gateway baru = tambah satu adapter di sini,
tidak perlu ubah views.py.
"""
import hashlib
import hmac

# Status kanonis kita (lihat sql/013_payment_gateway_resilience.sql):
# pending | settlement | expired | failed | refunded | chargeback

MIDTRANS_STATUS_MAP = {
    'capture': 'settlement',
    'settlement': 'settlement',
    'pending': 'pending',
    'deny': 'failed',
    'cancel': 'failed',
    'expire': 'expired',
    'refund': 'refunded',
    'partial_refund': 'refunded',
    'chargeback': 'chargeback',
    'partial_chargeback': 'chargeback',
}

XENDIT_STATUS_MAP = {
    'PAID': 'settlement',
    'SETTLED': 'settlement',
    'PENDING': 'pending',
    'EXPIRED': 'expired',
    'FAILED': 'failed',
    'STOPPED': 'failed',
    'REFUNDED': 'refunded',
}


class UnknownGatewayError(Exception):
    pass


def verify_midtrans_signature(payload, server_key):
    """signature_key = SHA512(order_id + status_code + gross_amount + ServerKey)."""
    expected = hashlib.sha512(
        f"{payload.get('order_id', '')}{payload.get('status_code', '')}"
        f"{payload.get('gross_amount', '')}{server_key}".encode('utf-8')
    ).hexdigest()
    return hmac.compare_digest(expected, payload.get('signature_key', ''))


def verify_xendit_token(request_token, callback_token):
    if not request_token or not callback_token:
        return False
    return hmac.compare_digest(request_token, callback_token)


def verify_signature(provider, payload, credentials, request_headers):
    if provider == 'midtrans':
        return verify_midtrans_signature(payload, credentials.get('server_key', ''))
    if provider == 'xendit':
        return verify_xendit_token(request_headers.get('X-Callback-Token', ''), credentials.get('callback_token', ''))
    raise UnknownGatewayError(f'Unknown provider: {provider}')


def extract_order_id(provider, payload):
    if provider == 'midtrans':
        return payload.get('order_id')
    if provider == 'xendit':
        return payload.get('external_id')
    raise UnknownGatewayError(f'Unknown provider: {provider}')


def extract_transaction_id(provider, payload):
    if provider == 'midtrans':
        return payload.get('transaction_id')
    if provider == 'xendit':
        return payload.get('id')
    raise UnknownGatewayError(f'Unknown provider: {provider}')


def extract_payment_method(provider, payload):
    if provider == 'midtrans':
        return payload.get('payment_type')
    if provider == 'xendit':
        return payload.get('payment_channel') or payload.get('payment_method')
    return None


def extract_raw_status(provider, payload):
    if provider == 'midtrans':
        return payload.get('transaction_status')
    if provider == 'xendit':
        return payload.get('status')
    raise UnknownGatewayError(f'Unknown provider: {provider}')


def normalize_status(provider, raw_status):
    if provider == 'midtrans':
        return MIDTRANS_STATUS_MAP.get(raw_status)
    if provider == 'xendit':
        return XENDIT_STATUS_MAP.get(raw_status)
    raise UnknownGatewayError(f'Unknown provider: {provider}')


# Status yang sudah final tidak boleh mundur ke status yang lebih awal —
# webhook gateway suka retry & bisa datang tidak berurutan (lihat komentar
# di sql/013). 'pending' adalah satu-satunya status non-final; begitu
# payment sudah di status final, hanya 'refunded'/'chargeback' (kejadian
# SETELAH settlement) yang boleh menimpanya.
FINAL_STATUSES = {'settlement', 'expired', 'failed', 'refunded', 'chargeback'}
POST_SETTLEMENT_STATUSES = {'refunded', 'chargeback'}


def should_apply_transition(current_status, incoming_status):
    if current_status == 'pending':
        return True
    if current_status in FINAL_STATUSES:
        return incoming_status in POST_SETTLEMENT_STATUSES
    return True
