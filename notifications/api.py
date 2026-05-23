"""
Notifications Admin API
-----------------------
All endpoints require is_staff=True (AdminBearer).
Base path: /api/notifications/

Endpoints:
  GET  /admin/channels/
  POST /admin/channels/
  GET  /admin/channels/{id}/
  PUT  /admin/channels/{id}/

  GET  /admin/templates/
  POST /admin/templates/
  GET  /admin/templates/{id}/
  PUT  /admin/templates/{id}/
  DELETE /admin/templates/{id}/

  GET  /admin/logs/
  GET  /admin/logs/{id}/
  GET  /admin/queue/
  POST /admin/queue/process/

  GET  /admin/variables/
  GET  /admin/event-types/
  POST /admin/templates/{id}/preview/
  POST /admin/templates/{id}/send-test/
"""

import logging
from typing import List, Optional

from django.http import JsonResponse
from ninja import Router
from pydantic import BaseModel

from core.auth import AdminBearer
from core.exceptions import AppException

from .models import (
    NotificationChannel,
    NotificationEventType,
    NotificationLog,
    NotificationQueue,
    NotificationTemplate,
)
from .schemas import (
    ChannelCreateIn,
    ChannelOut,
    ChannelUpdateIn,
    EventTypesOut,
    LogListOut,
    LogOut,
    PreviewTemplateIn,
    QueueListOut,
    QueueOut,
    SendTestIn,
    TemplateCreateIn,
    TemplateOut,
    TemplateUpdateIn,
    VariablesOut,
)
from .services import (
    get_available_variables,
    get_event_type_choices,
    process_queue_item,
    render_template,
    send_notification,
    process_pending_queue,
)

logger = logging.getLogger(__name__)

router = Router(tags=["Notifications Admin"])

_auth = AdminBearer()


# ── Pagination Helper ───────────────────────────────────────────────────────

def _paginate(qs, page: int, page_size: int):
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total = qs.count()
    start = (page - 1) * page_size
    total_pages = max(1, (total + page_size - 1) // page_size)
    return total, total_pages, qs[start: start + page_size]


# ═════════════════════════════════════════════════════════════════════════════
# Channels
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/channels/",
    auth=_auth,
    response=List[ChannelOut],
    summary="لیست کانال‌های اطلاع‌رسانی",
)
def list_channels(request):
    return [
        ChannelOut(
            id=c.id,
            name=c.name,
            name_display=c.get_name_display(),
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in NotificationChannel.objects.all()
    ]


@router.post(
    "/admin/channels/",
    auth=_auth,
    response=ChannelOut,
    summary="ایجاد کانال جدید",
)
def create_channel(request, payload: ChannelCreateIn):
    if NotificationChannel.objects.filter(name=payload.name).exists():
        return JsonResponse(
            {"error": True, "code": "duplicate", "message": "کانال با این نام قبلاً وجود دارد."},
            status=400,
        )
    channel = NotificationChannel.objects.create(
        name=payload.name,
        is_active=payload.is_active,
        config=payload.config,
    )
    return ChannelOut(
        id=channel.id,
        name=channel.name,
        name_display=channel.get_name_display(),
        is_active=channel.is_active,
        created_at=channel.created_at,
    )


@router.get(
    "/admin/channels/{channel_id}/",
    auth=_auth,
    response=ChannelOut,
    summary="جزئیات کانال",
)
def get_channel(request, channel_id: int):
    try:
        c = NotificationChannel.objects.get(pk=channel_id)
    except NotificationChannel.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "کانال یافت نشد."},
            status=404,
        )
    return ChannelOut(
        id=c.id,
        name=c.name,
        name_display=c.get_name_display(),
        is_active=c.is_active,
        created_at=c.created_at,
    )


@router.put(
    "/admin/channels/{channel_id}/",
    auth=_auth,
    response=ChannelOut,
    summary="بروزرسانی کانال",
)
def update_channel(request, channel_id: int, payload: ChannelUpdateIn):
    try:
        c = NotificationChannel.objects.get(pk=channel_id)
    except NotificationChannel.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "کانال یافت نشد."},
            status=404,
        )

    if payload.is_active is not None:
        c.is_active = payload.is_active
    if payload.config is not None:
        c.config = payload.config
    c.save()

    return ChannelOut(
        id=c.id,
        name=c.name,
        name_display=c.get_name_display(),
        is_active=c.is_active,
        created_at=c.created_at,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Templates
# ═════════════════════════════════════════════════════════════════════════════

def _template_to_out(t: NotificationTemplate) -> TemplateOut:
    return TemplateOut(
        id=t.id,
        event_type=t.event_type,
        event_type_display=t.get_event_type_display(),
        channel_id=t.channel_id,
        channel_name=t.channel.name if t.channel else "",
        subject=t.subject,
        template_text=t.template_text,
        is_active=t.is_active,
        description=t.description,
        updated_at=t.updated_at,
        created_at=t.created_at,
    )


@router.get(
    "/admin/templates/",
    auth=_auth,
    response=List[TemplateOut],
    summary="لیست قالب‌های پیام",
)
def list_templates(
    request,
    event_type: str = "",
    channel_id: Optional[int] = None,
):
    qs = NotificationTemplate.objects.select_related("channel").all()
    if event_type:
        qs = qs.filter(event_type=event_type)
    if channel_id:
        qs = qs.filter(channel_id=channel_id)
    return [_template_to_out(t) for t in qs]


@router.post(
    "/admin/templates/",
    auth=_auth,
    response=TemplateOut,
    summary="ایجاد قالب جدید",
)
def create_template(request, payload: TemplateCreateIn):
    try:
        channel = NotificationChannel.objects.get(pk=payload.channel_id)
    except NotificationChannel.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "کانال یافت نشد."},
            status=404,
        )

    if payload.event_type not in {c[0] for c in NotificationEventType.choices}:
        return JsonResponse(
            {"error": True, "code": "invalid_event", "message": "نوع رویداد نامعتبر است."},
            status=400,
        )

    if NotificationTemplate.objects.filter(
        event_type=payload.event_type, channel=channel
    ).exists():
        return JsonResponse(
            {"error": True, "code": "duplicate", "message": "قالبی برای این رویداد و کانال قبلاً وجود دارد."},
            status=400,
        )

    t = NotificationTemplate.objects.create(
        event_type=payload.event_type,
        channel=channel,
        template_text=payload.template_text,
        subject=payload.subject,
        is_active=payload.is_active,
        description=payload.description,
    )
    return _template_to_out(t)


@router.get(
    "/admin/templates/{template_id}/",
    auth=_auth,
    response=TemplateOut,
    summary="جزئیات قالب",
)
def get_template(request, template_id: int):
    try:
        t = NotificationTemplate.objects.select_related("channel").get(pk=template_id)
    except NotificationTemplate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "قالب یافت نشد."},
            status=404,
        )
    return _template_to_out(t)


@router.put(
    "/admin/templates/{template_id}/",
    auth=_auth,
    response=TemplateOut,
    summary="بروزرسانی قالب",
)
def update_template(request, template_id: int, payload: TemplateUpdateIn):
    try:
        t = NotificationTemplate.objects.select_related("channel").get(pk=template_id)
    except NotificationTemplate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "قالب یافت نشد."},
            status=404,
        )

    if payload.channel_id is not None:
        try:
            t.channel = NotificationChannel.objects.get(pk=payload.channel_id)
        except NotificationChannel.DoesNotExist:
            return JsonResponse(
                {"error": True, "code": "not_found", "message": "کانال یافت نشد."},
                status=404,
            )

    if payload.event_type is not None:
        t.event_type = payload.event_type
    if payload.template_text is not None:
        t.template_text = payload.template_text
    if payload.subject is not None:
        t.subject = payload.subject
    if payload.is_active is not None:
        t.is_active = payload.is_active
    if payload.description is not None:
        t.description = payload.description

    t.save()
    return _template_to_out(t)


@router.delete(
    "/admin/templates/{template_id}/",
    auth=_auth,
    summary="حذف قالب",
)
def delete_template(request, template_id: int):
    try:
        t = NotificationTemplate.objects.get(pk=template_id)
    except NotificationTemplate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "قالب یافت نشد."},
            status=404,
        )
    t.delete()
    return {"detail": "قالب با موفقیت حذف شد."}


# ═════════════════════════════════════════════════════════════════════════════
# Logs
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/logs/",
    auth=_auth,
    response=LogListOut,
    summary="لاگ اطلاع‌رسانی‌ها",
)
def list_logs(
    request,
    page: int = 1,
    page_size: int = 20,
    event_type: str = "",
    status: str = "",
    recipient: str = "",
):
    qs = NotificationLog.objects.select_related("channel", "user", "order").all()
    if event_type:
        qs = qs.filter(event_type=event_type)
    if status:
        qs = qs.filter(status=status)
    if recipient:
        qs = qs.filter(recipient__icontains=recipient)

    total, total_pages, page_qs = _paginate(qs, page, page_size)

    results = []
    for log in page_qs:
        results.append(LogOut(
            id=str(log.id),
            event_type=log.event_type,
            event_type_display=log.get_event_type_display(),
            channel_name=log.channel.name if log.channel else "",
            recipient=log.recipient,
            rendered_message=log.rendered_message,
            subject=log.subject,
            status=log.status,
            status_display=log.get_status_display(),
            error_message=log.error_message,
            sent_at=log.sent_at,
            retry_count=log.retry_count,
            created_at=log.created_at,
            user_phone=log.user.phone_number if log.user else None,
            order_id=log.order_id,
        ))

    return LogListOut(count=total, page=page, page_size=page_size, total_pages=total_pages, results=results)


@router.get(
    "/admin/logs/{log_id}/",
    auth=_auth,
    response=LogOut,
    summary="جزئیات لاگ",
)
def get_log(request, log_id: str):
    try:
        log = NotificationLog.objects.select_related("channel", "user", "order").get(pk=log_id)
    except (NotificationLog.DoesNotExist, ValueError):
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "لاگ یافت نشد."},
            status=404,
        )
    return LogOut(
        id=str(log.id),
        event_type=log.event_type,
        event_type_display=log.get_event_type_display(),
        channel_name=log.channel.name if log.channel else "",
        recipient=log.recipient,
        rendered_message=log.rendered_message,
        subject=log.subject,
        status=log.status,
        status_display=log.get_status_display(),
        error_message=log.error_message,
        sent_at=log.sent_at,
        retry_count=log.retry_count,
        created_at=log.created_at,
        user_phone=log.user.phone_number if log.user else None,
        order_id=log.order_id,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Queue
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/queue/",
    auth=_auth,
    response=QueueListOut,
    summary="صف اطلاع‌رسانی",
)
def list_queue(request, page: int = 1, page_size: int = 20, status: str = ""):
    qs = NotificationQueue.objects.select_related("template").all()
    if status:
        qs = qs.filter(status=status)

    total, total_pages, page_qs = _paginate(qs, page, page_size)

    results = []
    for item in page_qs:
        results.append(QueueOut(
            id=str(item.id),
            event_type=item.template.event_type if item.template else "",
            recipient=item.recipient,
            status=item.status,
            retry_count=item.retry_count,
            error_message=item.error_message,
            created_at=item.created_at,
            processed_at=item.processed_at,
        ))

    return QueueListOut(count=total, page=page, page_size=page_size, total_pages=total_pages, results=results)


@router.post(
    "/admin/queue/process/",
    auth=_auth,
    summary="پردازش صف اطلاع‌رسانی",
)
def process_queue(request, batch_size: int = 50):
    """پردازش دسته‌ای آیتم‌های pending در صف."""
    result = process_pending_queue(batch_size=batch_size)
    return {
        "detail": "صف پردازش شد.",
        "processed": result["processed"],
        "failed": result["failed"],
        "skipped": result["skipped"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# Utilities
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/variables/",
    auth=_auth,
    response=VariablesOut,
    summary="لیست متغیرهای داینامیک",
)
def list_variables(request, event_type: str = ""):
    """لیست متغیرهای داینامیک موجود برای یک رویداد یا همه رویدادها."""
    data = get_available_variables(event_type or None)
    if "event_type" in data:
        return VariablesOut(event_type=data["event_type"], variables=data["variables"])
    return VariablesOut(all_events=data.get("all_events", {}))


@router.get(
    "/admin/event-types/",
    auth=_auth,
    response=EventTypesOut,
    summary="لیست رویدادهای سیستمی",
)
def list_event_types(request):
    return EventTypesOut(choices=get_event_type_choices())


@router.post(
    "/admin/templates/{template_id}/preview/",
    auth=_auth,
    summary="پیش‌نمایش قالب",
)
def preview_template(request, template_id: int, payload: PreviewTemplateIn):
    """پیش‌نمایش قالب با متغیرهای داینامیک."""
    try:
        template = NotificationTemplate.objects.select_related("channel").get(pk=template_id)
    except NotificationTemplate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "قالب یافت نشد."},
            status=404,
        )

    rendered = render_template(
        template.template_text,
        template.event_type,
        user=request.auth,
        order=None,
        extra_context=payload.extra_context,
    )
    subject_rendered = ""
    if template.subject:
        subject_rendered = render_template(
            template.subject,
            template.event_type,
            user=request.auth,
            order=None,
            extra_context=payload.extra_context,
        )

    return {
        "subject": subject_rendered,
        "body": rendered,
        "channel": template.channel.name if template.channel else "",
        "event_type": template.event_type,
    }


@router.post(
    "/admin/templates/{template_id}/send-test/",
    auth=_auth,
    summary="ارسال تست قالب",
)
def send_test_template(request, template_id: int, payload: SendTestIn):
    """ارسال تست یک قالب به شماره مشخص."""
    try:
        template = NotificationTemplate.objects.select_related("channel").get(pk=template_id)
    except NotificationTemplate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "قالب یافت نشد."},
            status=404,
        )

    try:
        from accounts.models import User
        user = User.objects.get(phone_number=payload.phone_number)
    except User.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "کاربر با این شماره یافت نشد."},
            status=404,
        )

    logs = send_notification(
        event_type=template.event_type,
        user=user,
        order=None,
        extra_context=payload.extra_context,
        use_queue=False,
    )

    if logs:
        return {"detail": "پیام تست ارسال شد.", "log_id": str(logs[0].id)}
    return JsonResponse(
        {"error": True, "code": "send_failed", "message": "ارسال ناموفق بود."},
        status=400,
    )
