"""
Celery tasks for notification processing.
Replaces the cron-job based approach with async task queue.
"""
from celery import shared_task
import logging
from .services import process_pending_queue

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_notification_queue(self, batch_size: int = 50):
    """
    Process pending notifications from the queue.
    Can be called periodically via Celery Beat.
    
    Args:
        batch_size: Number of items to process in one batch
    """
    try:
        result = process_pending_queue(batch_size=batch_size)
        logger.info(
            f"[Celery] Processed notifications: {result['processed']} sent, "
            f"{result['failed']} failed, {result['skipped']} skipped"
        )
        return result
    except Exception as exc:
        logger.exception(f"[Celery] Failed to process notification queue: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_single_notification(template_id: int, user_id: int, order_id: int = None, extra_context: dict = None):
    """
    Send a single notification immediately (bypass queue).
    Useful for high-priority notifications.
    """
    from .models import NotificationTemplate, User, Order
    from .services import send_notification
    
    try:
        template = NotificationTemplate.objects.get(pk=template_id)
        user = User.objects.get(pk=user_id)
        order = Order.objects.get(pk=order_id) if order_id else None
        
        send_notification(
            event_type=template.event_type,
            user=user,
            order=order,
            extra_context=extra_context or {},
            use_queue=False,  # Send immediately
        )
        return {"status": "sent", "template_id": template_id, "user_id": user_id}
    except Exception as exc:
        logger.exception(f"[Celery] Failed to send single notification: {exc}")
        return {"status": "failed", "error": str(exc)}
