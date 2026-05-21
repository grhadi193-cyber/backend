from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address, OTPRecord


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["phone_number"]
    list_display = ["phone_number", "full_name", "email", "is_active", "is_staff", "date_joined"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["phone_number", "full_name", "email"]
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("اطلاعات شخصی", {"fields": ("full_name", "email")}),
        ("دسترسی‌ها", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("تاریخ‌ها", {"fields": ("date_joined",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("phone_number", "password1", "password2")}),
    )
    readonly_fields = ["date_joined"]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "province", "city", "postal_code", "is_default"]
    search_fields = ["user__phone_number", "city", "province"]
    list_filter = ["is_default", "province"]


@admin.register(OTPRecord)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "code", "created_at", "expires_at", "is_used"]
    list_filter = ["is_used"]
    search_fields = ["phone_number"]
    readonly_fields = ["phone_number", "code", "created_at", "expires_at", "is_used"]
