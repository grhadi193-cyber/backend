from django.contrib import admin

from sms.models import SMSLog


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "success", "sent_at", "short_message")
    list_filter = ("success", "sent_at")
    search_fields = ("recipient", "message", "error_message")
    readonly_fields = ("recipient", "message", "sent_at", "success", "error_message")
    ordering = ("-sent_at",)

    def short_message(self, obj: SMSLog) -> str:
        return obj.message[:60] + ("…" if len(obj.message) > 60 else "")

    short_message.short_description = "پیام"

    def has_add_permission(self, request):  # noqa: ANN001
        return False

    def has_change_permission(self, request, obj=None):  # noqa: ANN001
        return False
