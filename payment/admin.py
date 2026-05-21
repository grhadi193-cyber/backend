from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ("id", "order", "amount", "status", "ref_id", "created_at")
    list_filter   = ("status",)
    search_fields = ("ref_id", "order__id")
    readonly_fields = ("created_at", "gateway_response")
