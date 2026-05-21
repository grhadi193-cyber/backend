from django.db import models


class SiteSettings(models.Model):
    # ── فیلدهای جدید (فاز 18) ─────────────────────────────────────────────
    site_name        = models.CharField(max_length=200, default="فروشگاه من")
    logo             = models.ImageField(upload_to="site/", null=True, blank=True)
    banner_text      = models.CharField(max_length=500, blank=True)
    announcement     = models.TextField(blank=True)
    primary_color    = models.CharField(max_length=7, default="#01696f")
    maintenance_mode = models.BooleanField(default=False)
    social_instagram = models.URLField(blank=True)
    social_telegram  = models.URLField(blank=True)
    support_phone    = models.CharField(max_length=20, blank=True)

    # ── فیلدهای قدیمی — نگه‌داری شده ────────────────────────────────────
    hero_title  = models.CharField(max_length=200, blank=True, default="Welcome to our store")
    hero_text   = models.TextField(blank=True, default="Best products at best prices.")
    hero_banner = models.ImageField(upload_to="banners/", null=True, blank=True)
    about_us    = models.TextField(blank=True)

    class Meta:
        verbose_name        = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return "تنظیمات اصلی سایت"

    @classmethod
    def get(cls):
        """Singleton getter — همیشه ردیف pk=1 را برمی‌گرداند."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
