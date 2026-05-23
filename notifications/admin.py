from django.contrib import admin
from .models import NotificationChannel, NotificationTemplate, NotificationLog, NotificationQueue


@admin.register(NotificationChannel)
class NotificationChannelAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active", "name"]
    search_fields = ["name"]


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ["event_type", "channel", "is_active", "updated_at"]
    list_filter = ["event_type", "channel", "is_active"]
    search_fields = ["subject", "template_text"]
    list_editable = ["is_active"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["event_type", "channel", "recipient", "status", "created_at"]
    list_filter = ["event_type", "status", "channel", "created_at"]
    search_fields = ["recipient", "rendered_message"]
    readonly_fields = ["created_at", "sent_at"]


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ["template", "recipient", "status", "retry_count", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["recipient"]
    readonly_fields = ["created_at"]
