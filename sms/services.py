"""
SMS Service Layer.
SMSLog fields: recipient, message, success, error_message, sent_at
- DEBUG: print to console + write SMSLog, never call Kavenegar
- PRODUCTION: call Kavenegar + write SMSLog
- No public API. Called explicitly from other services (no signals).
"""

import logging
from django.conf import settings
from .models import SMSLog

logger = logging.getLogger(__name__)


def _send(phone_number: str, message: str, sms_type: str) -> None:
    if settings.DEBUG:
        print(f"[SMS][DEBUG] To={phone_number} Type={sms_type}: {message}")
        SMSLog.objects.create(
            recipient=phone_number,
            message=message,
            success=True,
        )
        return

    # Production — Kavenegar
    try:
        from kavenegar import KavenegarAPI
        api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
        api.sms_send({"receptor": phone_number, "message": message})
        SMSLog.objects.create(
            recipient=phone_number,
            message=message,
            success=True,
        )
        logger.info("[SMS] Sent %s to %s", sms_type, phone_number)
    except Exception as exc:
        SMSLog.objects.create(
            recipient=phone_number,
            message=message,
            success=False,
            error_message=str(exc),
        )
        logger.exception("[SMS] Failed to send %s to %s: %s", sms_type, phone_number, exc)
        raise


def send_otp(phone_number: str, code: str) -> None:
    _send(phone_number, f"کد تأیید شما: {code}", sms_type="OTP")


def send_order_success_sms(phone_number: str, order_id: int) -> None:
    """Called explicitly from payment.services after successful payment."""
    _send(
        phone_number,
        f"سفارش شماره {order_id} شما با موفقیت ثبت و پرداخت شد. ممنون از خریدتان.",
        sms_type="ORDER_SUCCESS",
    )
