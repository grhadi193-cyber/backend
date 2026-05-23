"""
Management command to process pending notification queue.

Usage:
    python manage.py process_notification_queue --batch-size=50

Recommended: Run this command via cron every 1-5 minutes.
"""

from django.core.management.base import BaseCommand
from notifications.services import process_pending_queue


class Command(BaseCommand):
    help = "Process pending notification queue items"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of queue items to process per run (default: 50)",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        self.stdout.write(f"Processing notification queue (batch_size={batch_size})...")

        result = process_pending_queue(batch_size=batch_size)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done! Processed: {result['processed']}, Failed: {result['failed']}, Skipped: {result['skipped']}"
            )
        )
