from django.db import models


class SMSLog(models.Model):
    recipient = models.CharField(max_length=20, verbose_name="شماره گیرنده")
    message = models.TextField(verbose_name="متن پیام")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")
    success = models.BooleanField(default=False, verbose_name="موفق")
    error_message = models.TextField(
        null=True, blank=True, verbose_name="پیام خطا"
    )

    class Meta:
        verbose_name = "لاگ پیامک"
        verbose_name_plural = "لاگ‌های پیامک"
        ordering = ["-sent_at"]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"[{status}] {self.recipient} — {self.sent_at:%Y-%m-%d %H:%M}"
