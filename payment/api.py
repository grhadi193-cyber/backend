import logging

from django.http import JsonResponse
from ninja import Router, Query

from core.auth import AuthBearer
from .schemas import InitiatePaymentIn, InitiatePaymentOut, VerifyCallbackIn
from .orchestrator import start_payment, verify_payment
from .models import Transaction
from store.models import Order

logger = logging.getLogger(__name__)

router = Router(tags=["Payment"])

_auth = AuthBearer()


@router.post("/initiate", response=InitiatePaymentOut, auth=_auth)
def initiate_payment(request, payload: InitiatePaymentIn):
    """
    شروع پرداخت برای یک سفارش موجود.
    سفارش باید متعلق به کاربر احراز‌هویت‌شده باشد.
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
    Endpoint ریدایرکت درگاه پرداخت.
    ابتدا cb_token را تأیید می‌کند تا از جعل وضعیت جلوگیری شود.

    NOTE: در production این پاسخ‌های JSON را با HttpResponseRedirect
    به frontend خود جایگزین کن، مثلاً:
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect("https://yourfrontend.com/payment/success?order=...")
    """
    raw = dict(request.GET)
    raw_flat = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in raw.items()}

    # ── تعیین transaction_id ───────────────────────────────────────────────
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
            txn = Transaction.objects.filter(ref_id=authority, status="pending").first()
            if txn is None:
                return JsonResponse(
                    {"error": True, "code": "not_found", "message": "Transaction not found for given Authority."},
                    status=404,
                )
            transaction_id = txn.pk

    # ── تأیید cb_token (یک‌بارمصرف) ─────────────────────────────────────────
    transaction = Transaction.objects.filter(pk=transaction_id).first()
    if not transaction or transaction.callback_token != params.cb_token:
        logger.warning(
            f"[Payment] callback token mismatch for transaction_id={transaction_id} "
            f"provided={params.cb_token!r}"
        )
        return JsonResponse(
            {"error": True, "code": "invalid_token", "message": "درخواست نامعتبر است."},
            status=400,
        )

    # token را پاک کن تا یک‌بارمصرف باشد
    Transaction.objects.filter(pk=transaction_id).update(callback_token="")

    # ── تأیید پرداخت در درگاه ────────────────────────────────────────────────
    success = verify_payment(transaction_id, raw_flat)

    if success:
        return JsonResponse({"status": "paid", "transaction_id": transaction_id})
    return JsonResponse({"status": "failed", "transaction_id": transaction_id}, status=402)
