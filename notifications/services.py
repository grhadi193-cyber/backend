"""
Notification Service Layer
--------------------------
- render_template: رندر قالب با متغیرهای داینامیک
- send_notification: ارسال نوتیفیکیشن (مستقیم یا از طریق صف)
- process_queue_item: پردازش یک آیتم از صف
- queue_notification: افزودن به صف
- get_available_variables: لیست متغیرهای موجود برای هر رویداد
"""

import logging
import re
from typing import Dict, List, Optional
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from .models import (
    NotificationChannel,
    NotificationEventType,
    NotificationLog,
    NotificationQueue,
    NotificationTemplate,
)

logger = logging.getLogger(__name__)


# ── Variable Extraction & Rendering ────────────────────────────────────────

# متغیرهای پیش‌فرض برای هر رویداد
DEFAULT_VARIABLES = {
    "user_registered": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "user_phone": lambda user, order: user.phone_number,
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_created": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "order_total_price": lambda user, order: _format_price(order.total_price),
        "order_shipping_cost": lambda user, order: _format_price(order.shipping_cost),
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_paid": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "order_total_price": lambda user, order: _format_price(order.total_price),
        "payment_amount": lambda user, order: _format_price(order.total_price),
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_confirmed": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "order_total_price": lambda user, order: _format_price(order.total_price),
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_processing": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_shipped": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "postal_tracking": lambda user, order: order.postal_tracking or "---",
        "carrier_name": lambda user, order: order.carrier_name or "---",
        "tracking_url": lambda user, order: _build_tracking_url(order),
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_delivered": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "site_name": lambda user, order: _get_site_name(),
    },
    "order_cancelled": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "order_total_price": lambda user, order: _format_price(order.total_price),
        "site_name": lambda user, order: _get_site_name(),
    },
    "payment_failed": {
        "user_full_name": lambda user, order: user.full_name or "کاربر",
        "order_id": lambda user, order: str(order.pk),
        "order_tracking_number": lambda user, order: order.tracking_number,
        "site_name": lambda user, order: _get_site_name(),
    },
}


def _get_site_name() -> str:
    try:
        from core.models import SiteSettings
        return SiteSettings.get().site_name
    except Exception:
        return "فروشگاه"


def _format_price(value) -> str:
    if value is None:
        return "0"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def _build_tracking_url(order) -> str:
    if order.postal_tracking and order.carrier_name:
        return f"https://tracking.example.com/?code={order.postal_tracking}"
    return ""


def _extract_variables(template_text: str) -> List[str]:
    """استخراج نام متغیرها از قالب با فرمت {variable_name}"""
    pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
    return re.findall(pattern, template_text)


def render_template(
    template_text: str,
    event_type: str,
    user,
    order,
    extra_context: Optional[Dict] = None,
) -> str:
    """
    رندر قالب با متغیرهای داینامیک.
    متغیرها از DEFAULT_VARIABLES خوانده شده و با extra_context ادغام می‌شوند.
    """
    variable_names = _extract_variables(template_text)
    context = {}

    event_vars = DEFAULT_VARIABLES.get(event_type, {})

    for var_name in variable_names:
        if extra_context and var_name in extra_context:
            context[var_name] = str(extra_context[var_name])
        elif var_name in event_vars:
            try:
                context[var_name] = str(event_vars[var_name](user, order))
            except Exception as exc:
                logger.warning("[Notification] Variable %s error: %s", var_name, exc)
                context[var_name] = ""
        else:
            context[var_name] = ""

    # Add any extra context that wasn't in template but may be useful
    if extra_context:
        for key, value in extra_context.items():
            if key not in context:
                context[key] = str(value)

    def _replace(match):
        var_name = match.group(1)
        return context.get(var_name, match.group(0))

    return re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', _replace, template_text)


# ── Core Send Function ──────────────────────────────────────────────────────

def send_notification(
    event_type: str,
    user,
    order=None,
    extra_context: Optional[Dict] = None,
    use_queue: bool = True,
) -> List[NotificationLog]:
    """
    ارسال نوتیفیکیشن برای یک رویداد.
    تمام قالب‌های فعال برای این رویداد را پیدا کرده و ارسال می‌کند.

    Args:
        event_type: یکی از NotificationEventType.values
        user: instance از User
        order: instance از Order (اختیاری)
        extra_context: دیکشنری با مقادیر اضافی
        use_queue: اگر True، پیام‌ها به صف اضافه می‌شوند

    Returns:
        لیست NotificationLog ایجاد شده
    """
    if not user or not user.phone_number:
        logger.warning("[Notification] No user or phone number for event %s", event_type)
        return []

    templates = (
        NotificationTemplate.objects
        .filter(event_type=event_type, is_active=True)
        .select_related("channel")
    )

    if not templates.exists():
        logger.info("[Notification] No active templates for event %s", event_type)
        return []

    logs = []
    for template in templates:
        if not template.channel.is_active:
            continue

        if use_queue:
            queue_item = queue_notification(
                template=template,
                user=user,
                order=order,
                extra_context=extra_context,
            )
            # ایجاد لاگ pending
            log = NotificationLog.objects.create(
                template=template,
                event_type=event_type,
                channel=template.channel,
                recipient=user.phone_number,
                rendered_message="",
                subject=template.subject,
                status="pending",
                user=user,
                order=order,
                context_data={
                    **(extra_context or {}),
                    "queue_id": str(queue_item.id),
                },
            )
            logs.append(log)
        else:
            # ارسال مستقیم
            log = _execute_send(
                template=template,
                event_type=event_type,
                user=user,
                order=order,
                extra_context=extra_context,
            )
            logs.append(log)

    return logs


# ── Queue Management ────────────────────────────────────────────────────────

def queue_notification(
    template: NotificationTemplate,
    user,
    order=None,
    extra_context: Optional[Dict] = None,
) -> NotificationQueue:
    """افزودن یک نوتیفیکیشن به صف ارسال"""
    return NotificationQueue.objects.create(
        template=template,
        recipient=user.phone_number,
        user=user,
        order=order,
        context_data=extra_context or {},
    )


def process_queue_item(queue_item: NotificationQueue) -> NotificationLog:
    """پردازش یک آیتم از صف و ارسال آن"""
    queue_item.status = "processing"
    queue_item.save(update_fields=["status"])

    try:
        log = _execute_send(
            template=queue_item.template,
            event_type=queue_item.template.event_type,
            user=queue_item.user,
            order=queue_item.order,
            extra_context=queue_item.context_data,
        )
        queue_item.status = "completed"
        queue_item.processed_at = timezone.now()
        queue_item.save(update_fields=["status", "processed_at"])
        return log
    except Exception as exc:
        queue_item.retry_count += 1
        queue_item.error_message = str(exc)

        if queue_item.retry_count >= 3:
            queue_item.status = "failed"
        else:
            queue_item.status = "pending"

        queue_item.save(update_fields=["status", "retry_count", "error_message"])
        raise


def process_pending_queue(batch_size: int = 50) -> dict:
    """
    پردازش دسته‌ای آیتم‌های pending در صف.
    برای استفاده در cron job یا management command.

    Returns:
        dict با کلیدهای processed, failed, skipped
    """
    items = (
        NotificationQueue.objects
        .filter(status="pending")
        .select_related("template", "user", "order")
        .order_by("created_at")[:batch_size]
    )

    result = {"processed": 0, "failed": 0, "skipped": 0}

    for item in items:
        if not item.user:
            item.status = "failed"
            item.error_message = "User deleted"
            item.save(update_fields=["status", "error_message"])
            result["skipped"] += 1
            continue

        try:
            process_queue_item(item)
            result["processed"] += 1
        except Exception as exc:
            logger.exception("[NotificationQueue] Failed to process %s: %s", item.id, exc)
            result["failed"] += 1

    return result


# ── Internal Execution ──────────────────────────────────────────────────────

def _execute_send(
    template: NotificationTemplate,
    event_type: str,
    user,
    order=None,
    extra_context: Optional[Dict] = None,
) -> NotificationLog:
    """اجرای واقعی ارسال نوتیفیکیشن"""

    rendered_message = render_template(
        template.template_text,
        event_type,
        user,
        order,
        extra_context,
    )
    rendered_subject = render_template(
        template.subject,
        event_type,
        user,
        order,
        extra_context,
    ) if template.subject else ""

    # Send via the appropriate channel
    channel_name = template.channel.name if template.channel else "sms"

    if channel_name == "sms":
        _send_via_sms(user.phone_number, rendered_message)
    elif channel_name == "email":
        _send_via_email(user.email, rendered_subject, rendered_message)
    elif channel_name == "whatsapp":
        _send_via_whatsapp(user.phone_number, rendered_message)
    elif channel_name == "push":
        _send_via_push(user, rendered_subject, rendered_message)

    log = NotificationLog.objects.create(
        template=template,
        event_type=event_type,
        channel=template.channel,
        recipient=user.phone_number,
        rendered_message=rendered_message,
        subject=rendered_subject,
        status="sent",
        sent_at=timezone.now(),
        user=user,
        order=order,
        context_data=extra_context or {},
    )

    logger.info("[Notification] %s sent to %s via %s", event_type, user.phone_number, channel_name)
    return log


# ── Channel Senders ─────────────────────────────────────────────────────────

def _send_via_sms(phone_number: str, message: str) -> None:
    """ارسال پیامک از طریق سرویس موجود Kavenegar"""
    from sms.services import _send as send_sms_raw
    send_sms_raw(phone_number, message, sms_type="NOTIFICATION")


def _send_via_email(email: str, subject: str, message: str) -> None:
    """ارسال ایمیل — placeholder برای پیاده‌سازی آینده"""
    if not email:
        logger.warning("[NotificationEmail] No email address provided")
        return
    logger.info("[NotificationEmail] To=%s Subject=%s", email, subject)


def _send_via_whatsapp(phone_number: str, message: str) -> None:
    """ارسال واتساپ — placeholder برای پیاده‌سازی آینده"""
    logger.info("[NotificationWhatsApp] To=%s: %s...", phone_number, message[:50])


def _send_via_push(user, title: str, message: str) -> None:
    """ارسال پوش نوتیفیکیشن — placeholder برای پیاده‌سازی آینده"""
    logger.info("[NotificationPush] To user=%s: %s", user.pk, title)


# ── Variable Info Helper ────────────────────────────────────────────────────

def get_available_variables(event_type: Optional[str] = None) -> Dict:
    """
    لیست متغیرهای داینامیک موجود برای هر رویداد.
    برای نمایش در پنل ادمین.
    """
    if event_type and event_type in DEFAULT_VARIABLES:
        return {
            "event_type": event_type,
            "variables": list(DEFAULT_VARIABLES[event_type].keys()),
        }

    all_vars = {}
    for et, vars_dict in DEFAULT_VARIABLES.items():
        all_vars[et] = list(vars_dict.keys())

    return {"all_events": all_vars}


def get_event_type_choices() -> List[Dict]:
    """لیست رویدادهای موجود برای نمایش در API"""
    return [
        {"value": choice[0], "label": choice[1]}
        for choice in NotificationEventType.choices
    ]
