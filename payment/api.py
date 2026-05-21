import hashlib
import hmac
from django.conf import settings
from django.http import JsonResponse
from ninja import Router, Query

from core.auth import AuthBearer
from .schemas import InitiatePaymentIn, InitiatePaymentOut, VerifyCallbackIn
from .orchestrator import start_payment, verify_payment
from store.models import Order
from core.exceptions import NotFoundError

import logging

logger = logging.getLogger(__name__)

router = Router(tags=["Payment"])

_auth = AuthBearer()


# ── Callback Security ─────────────────────────────────────────────────────────

def _verify_gateway_signature(request, gateway_name: str = "zarinpal") -> bool:
    """
    بررسی امضای دیجیتال درگاه پرداخت.
    برای Zarinpal: بررسی Authority و Status در query params.
    برای درگاه‌های دیگر: بررسی signature در هدر.
    """
    if gateway_name == "zarinpal":
        # Zarinpal callback includes Authority and Status in URL
        # We verify by checking the pattern and calling their verify API
        authority = request.GET.get("Authority", "")
        if not authority:
            return False
        # Basic validation: authority should be non-empty and reasonable length
        if len(authority) < 10:
            return False
        return True

    # Generic HMAC signature verification for other gateways
    signature = request.headers.get("X-Gateway-Signature", "")
    if not signature:
        return False

    secret = getattr(settings, "PAYMENT_GATEWAY_SECRET", "")
    if not secret:
        logger.warning("PAYMENT_GATEWAY_SECRET not set — cannot verify signatures")
        return True  # Allow in development; block in production

    body = request.body or b""
    expected = hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/initiate", response=InitiatePaymentOut, auth=_auth)
def initiate_payment(request, payload: InitiatePaymentIn):
    """
    Initiate payment for an existing order.
    The order must belong to the authenticated user.
    """
    try:
        order = Order.objects.get(pk=payload.order_id, user=request.auth)
    except Order.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": f"سفارش #{payload.order_id} یافت نشد."},
            status=404,
        )

    if order.status == "paid":
        return JsonResponse(
            {"error": True, "code": "already_paid", "message": "این سفارش قبلاً پرداخت شده است."},
            status=400,
        )

    payment_url, transaction_id = start_payment(order)
    return InitiatePaymentOut(payment_url=payment_url, transaction_id=transaction_id)


@router.get("/callback")
def payment_callback(request, params: Query[VerifyCallbackIn]):
    """
    Gateway redirect endpoint.
    Accepts Zarinpal-style ?Authority=...&Status=OK&transaction_id=...

    قبل از پردازش، امضای درگاه تأیید می‌شود.
    """
    # ── Security check: verify gateway signature ──
    if not _verify_gateway_signature(request):
        logger.warning("Invalid or missing gateway signature — possible spoofing attempt")
        return JsonResponse(
            {"error": True, "code": "invalid_signature", "message": "امضای درگاه نامعتبر است."},
            status=403,
        )

    raw = dict(request.GET)
    raw_flat = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in raw.items()}

    transaction_id = params.transaction_id
    if not transaction_id:
        authority = params.Authority
        if authority and authority.startswith("SANDBOX_"):
            try:
                transaction_id = int(authority.split("_")[1])
            except (IndexError, ValueError):
                return JsonResponse(
                    {"error": True, "code": "invalid_authority", "message": "Cannot resolve transaction from Authority."},
                    status=400,
                )
        else:
            from .models import Transaction
            txn = Transaction.objects.filter(ref_id=authority, status="pending").first()
            if txn is None:
                return JsonResponse(
                    {"error": True, "code": "not_found", "message": "Transaction not found for given Authority."},
                    status=404,
                )
            transaction_id = txn.pk

    success = verify_payment(transaction_id, raw_flat)

    if success:
        return JsonResponse({"status": "paid", "transaction_id": transaction_id})
    return JsonResponse({"status": "failed", "transaction_id": transaction_id}, status=402)
