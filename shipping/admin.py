from django.contrib import admin

from .models import ShippingZone, ShippingMethod


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display  = ("name", "province_count")
    search_fields = ("name",)

    @admin.display(description="تعداد استان‌ها")
    def province_count(self, obj):
        return len(obj.provinces) if obj.provinces else 0


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display   = ("name", "slug", "zone", "base_cost", "cost_per_kg",
                      "free_above", "min_days", "max_days", "is_active")
    list_editable  = ("is_active", "base_cost", "cost_per_kg")
    list_filter    = ("is_active", "zone")
    search_fields  = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields  = ("zone",)
