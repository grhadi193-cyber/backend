from django.contrib import admin

from core.models import SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """
    SiteSettings singleton — در پنل ادمین Django قابل ویرایش.
    کاربر نمی‌تواند ردیف جدید اضافه یا حذف کند؛ فقط ردیف pk=1 موجود است.
    """

    fieldsets = (
        ("هویت سایت", {
            "fields": ("site_name", "logo", "primary_color"),
        }),
        ("محتوای صفحه اصلی", {
            "fields": ("banner_text", "announcement", "hero_title", "hero_text", "hero_banner", "about_us"),
        }),
        ("شبکه‌های اجتماعی و پشتیبانی", {
            "fields": ("social_instagram", "social_telegram", "support_phone"),
        }),
        ("وضعیت سایت", {
            "fields": ("maintenance_mode",),
        }),
    )

    def has_add_permission(self, request):
        """فقط یک ردیف مجاز است."""
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
