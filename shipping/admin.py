from django.contrib import admin

from .models import (
    ShippingZone,
    ShippingMethod,
    Province,
    City,
    ShippingRate,
)


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_active"]
    search_fields = ["name"]
    list_filter = ["is_active"]
    list_editable = ["is_active"]


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "province", "code", "is_active"]
    search_fields = ["name", "province__name"]
    list_filter = ["province", "is_active"]
    list_editable = ["is_active"]


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "province_count", "is_active")
    search_fields = ("name",)
    list_editable = ["is_active"]

    @admin.display(description="تعداد استان‌ها")
    def province_count(self, obj):
        return len(obj.provinces) if obj.provinces else 0


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = (
        "name", "slug", "carrier_name", "zone", "base_cost", "cost_per_kg",
        "free_above", "min_days", "max_days", "is_active",
    )
    list_editable = ("is_active", "base_cost", "cost_per_kg")
    list_filter = ("is_active", "zone")
    search_fields = ("name", "slug", "carrier_name")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ("zone",)


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = [
        "shipping_method", "province", "city", "weight_min", "weight_max", "cost", "is_active"
    ]
    list_editable = ["cost", "is_active"]
    list_filter = ["shipping_method", "province", "is_active"]
    search_fields = ["province__name", "city__name"]
    raw_id_fields = ["shipping_method", "province", "city"]
