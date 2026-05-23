import uuid
from django.db import models
from django.conf import settings


# ── NotificationChannel ─────────────────────────────────────────────────────

class NotificationChannel(models.Model):
    """کانال‌های ارسال نوتیفیکیشن (SMS, Email, WhatsApp, Push)"""

    CHANNEL_CHOICES = [
        ("sms", "پیامک"),
        ("email", "ایمیل"),
        ("whatsapp", "واتساپ"),
        ("push", "پوش نوتیفیکیشن"),
    ]

    name = models.CharField(max_length=50, choices=CHANNEL_CHOICES, unique=True, verbose_name="نام کانال")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    config = models.JSONField(default=dict, blank=True, verbose_name="تنظیمات")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کانال اطلاع‌رسانی"
        verbose_name_plural = "کانال‌های اطلاع‌رسانی"

    def __str__(self):
        return self.get_name_display()


# ── NotificationEventType ───────────────────────────────────────────────────

class NotificationEventType(models.TextChoices):
    """رویدادهای سیستمی که برای هرکدام می‌توان نوتیفیکیشن تعریف کرد"""

    USER_REGISTERED = "user_registered", "ثبت‌نام کاربر"
    ORDER_CREATED = "order_created", "ثبت سفارش"
    ORDER_PAID = "order_paid", "پرداخت سفارش"
    ORDER_CONFIRMED = "order_confirmed", "تایید سفارش"
    ORDER_PROCESSING = "order_processing", "آماده‌سازی سفارش"
    ORDER_SHIPPED = "order_shipped", "تحویل به پست/پیک"
    ORDER_DELIVERED = "order_delivered", "تحویل نهایی"
    ORDER_CANCELLED = "order_cancelled", "لغو سفارش"
    PAYMENT_FAILED = "payment_failed", "پرداخت ناموفق"


# ── NotificationTemplate ────────────────────────────────────────────────────

class NotificationTemplate(models.Model):
    """
    قالب پیام‌های اطلاع‌رسانی.
    هر قالب برای یک رویداد و یک کانال مشخص تعریف می‌شود.
    از متغیرهای داینامیک پشتیبانی می‌کند.
    """

    event_type = models.CharField(
        max_length=30,
        choices=NotificationEventType.choices,
        verbose_name="نوع رویداد",
    )
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.CASCADE,
        related_name="templates",
        verbose_name="کانال",
    )
    subject = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="موضوع",
        help_text="برای ایمیل استفاده می‌شود",
    )
    template_text = models.TextField(
        verbose_name="متن قالب",
        help_text="از {نام_متغیر} برای متغیرهای داینامیک استفاده کنید",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین بروزرسانی")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "قالب پیام"
        verbose_name_plural = "قالب‌های پیام"
        unique_together = [["event_type", "channel"]]
        ordering = ["event_type", "channel__name"]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.channel}"


# ── NotificationLog ─────────────────────────────────────────────────────────

class NotificationLog(models.Model):
    """لاگ تمام ارسال‌های اطلاع‌رسانی"""

    STATUS_CHOICES = [
        ("pending", "در صف"),
        ("sent", "ارسال شده"),
        ("failed", "ناموفق"),
        ("retrying", "در حال تلاش مجدد"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name="قالب",
    )
    event_type = models.CharField(max_length=30, choices=NotificationEventType.choices, verbose_name="نوع رویداد")
    channel = models.ForeignKey(
        NotificationChannel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
        verbose_name="کانال",
    )
    recipient = models.CharField(max_length=100, verbose_name="گیرنده", db_index=True)
    rendered_message = models.TextField(verbose_name="متن نهایی")
    subject = models.CharField(max_length=255, blank=True, default="", verbose_name="موضوع")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="وضعیت")
    error_message = models.TextField(blank=True, default="", verbose_name="پیام خطا")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ارسال")
    retry_count = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد تلاش مجدد")
    context_data = models.JSONField(default=dict, blank=True, verbose_name="داده‌های متن")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name="کاربر",
    )
    order = models.ForeignKey(
        "store.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_logs",
        verbose_name="سفارش",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")

    class Meta:
        verbose_name = "لاگ اطلاع‌رسانی"
        verbose_name_plural = "لاگ‌های اطلاع‌رسانی"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["event_type", "created_at"]),
            models.Index(fields=["recipient", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.event_type} → {self.recipient}"


# ── NotificationQueue ───────────────────────────────────────────────────────

class NotificationQueue(models.Model):
    """صف ارسال نوتیفیکیشن — برای پردازش دسته‌ای و جلوگیری از overload"""

    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("processing", "در حال پردازش"),
        ("completed", "تکمیل شده"),
        ("failed", "ناموفق"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.CASCADE,
        related_name="queue_items",
        verbose_name="قالب",
    )
    recipient = models.CharField(max_length=100, verbose_name="گیرنده")
    context_data = models.JSONField(default=dict, verbose_name="داده‌های متن")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_queue",
        verbose_name="کاربر",
    )
    order = models.ForeignKey(
        "store.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notification_queue",
        verbose_name="سفارش",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="وضعیت")
    error_message = models.TextField(blank=True, default="", verbose_name="پیام خطا")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان پردازش")
    retry_count = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد تلاش")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")

    class Meta:
        verbose_name = "آیتم صف اطلاع‌رسانی"
        verbose_name_plural = "صف اطلاع‌رسانی"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.template.event_type} → {self.recipient}"
