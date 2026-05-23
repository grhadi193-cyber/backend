from decimal import Decimal
from django.db import models
from django.utils.text import slugify
import json
import os


# ── Province ────────────────────────────────────────────────────────────────

class Province(models.Model):
    """استان‌های ایران — از JSON بارگذاری می‌شوند"""

    name = models.CharField(max_length=64, unique=True, verbose_name="نام استان")
    code = models.CharField(max_length=10, blank=True, verbose_name="کد استان")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "استان"
        verbose_name_plural = "استان‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ── City ────────────────────────────────────────────────────────────────────

class City(models.Model):
    """شهرهای ایران — متعلق به یک استان"""

    province = models.ForeignKey(
        Province, on_delete=models.CASCADE, related_name="cities", verbose_name="استان"
    )
    name = models.CharField(max_length=64, verbose_name="نام شهر")
    code = models.CharField(max_length=10, blank=True, verbose_name="کد شهر")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "شهر"
        verbose_name_plural = "شهرها"
        ordering = ["name"]
        unique_together = [["province", "name"]]

    def __str__(self):
        return f"{self.name} ({self.province.name})"


# ── ShippingZone ────────────────────────────────────────────────────────────

class ShippingZone(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام منطقه")
    provinces = models.JSONField(verbose_name="لیست استان‌ها")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "منطقه ارسال"
        verbose_name_plural = "مناطق ارسال"

    def __str__(self):
        return self.name


# ── ShippingMethod ──────────────────────────────────────────────────────────

class ShippingMethod(models.Model):
    name = models.CharField(max_length=128, verbose_name="نام روش")
    slug = models.SlugField(max_length=128, unique=True, blank=True, verbose_name="اسلاگ")
    carrier_name = models.CharField(max_length=100, blank=True, default="", verbose_name="نام پستی/پیک")
    tracking_url_template = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="قالب لینک رهگیری",
        help_text="مثال: https://tracking.post.ir/?code={tracking_code}",
    )
    base_cost = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="هزینه پایه")
    cost_per_kg = models.DecimalField(max_digits=8, decimal_places=0, default=0, verbose_name="هزینه هر کیلوگرم اضافی")
    free_above = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name="رایگان بالای")
    min_days = models.PositiveSmallIntegerField(default=2, verbose_name="حداقل روز")
    max_days = models.PositiveSmallIntegerField(default=7, verbose_name="حداکثر روز")
    zone = models.ForeignKey(
        ShippingZone, on_delete=models.CASCADE, null=True, blank=True,
        related_name="methods", verbose_name="منطقه"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "روش ارسال"
        verbose_name_plural = "روش‌های ارسال"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# ── ShippingRate ────────────────────────────────────────────────────────────

class ShippingRate(models.Model):
    """
    تعرفه ارسال بر اساس استان + شهر + بازه وزنی.
    اگر شهر null باشد، برای کل استان اعمال می‌شود.
    """

    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.CASCADE, related_name="rates", verbose_name="روش ارسال"
    )
    province = models.ForeignKey(
        Province, on_delete=models.CASCADE, related_name="shipping_rates", verbose_name="استان"
    )
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, null=True, blank=True,
        related_name="shipping_rates", verbose_name="شهر"
    )
    weight_min = models.DecimalField(
        max_digits=8, decimal_places=3, default=0, verbose_name="حداقل وزن (kg)"
    )
    weight_max = models.DecimalField(
        max_digits=8, decimal_places=3, default=0, verbose_name="حداکثر وزن (kg)"
    )
    cost = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="هزینه")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "تعرفه ارسال"
        verbose_name_plural = "تعرفه‌های ارسال"
        ordering = ["province", "city", "weight_min"]
        unique_together = [["shipping_method", "province", "city", "weight_min"]]

    def __str__(self):
        city_str = f" — {self.city.name}" if self.city else ""
        return f"{self.shipping_method.name} — {self.province.name}{city_str} [{self.weight_min}-{self.weight_max}kg]"


# ── Utility: Load Provinces/Cities from JSON ──────────────────────────────

def load_provinces_and_cities_from_json():
    """بارگذاری استان‌ها و شهرها از فایل JSON. فقط رکوردهای جدید اضافه می‌کند."""
    json_path = os.path.join(os.path.dirname(__file__), "iran_provinces_cities.json")
    if not os.path.exists(json_path):
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for prov_data in data.get("provinces", []):
        province, _ = Province.objects.get_or_create(
            name=prov_data["name"],
            defaults={"code": str(prov_data["id"])},
        )
        for city_data in prov_data.get("cities", []):
            City.objects.get_or_create(
                province=province,
                name=city_data["name"],
                defaults={"code": str(city_data["id"])},
            )
