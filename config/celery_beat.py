"""
Celery Beat schedule configuration.
Run with: celery -A config beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
Or use this static schedule for simple deployments.
"""
from celery.schedules import crontab

# Schedule for processing notification queue every 5 minutes
NOTIFICATION_QUEUE_SCHEDULE = {
    'process-notifications-every-5-minutes': {
        'task': 'notifications.tasks.process_notification_queue',
        'schedule': crontab(minute='*/5'),
        'kwargs': {'batch_size': 50},
    },
    
    # Daily cleanup of old logs (optional)
    'cleanup-old-logs-daily': {
        'task': 'notifications.tasks.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
    },
}
