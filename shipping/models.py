from django.db import models
from django.utils.text import slugify


class ShippingZone(models.Model):
    name = models.CharField(max_length=100)
    provinces = models.JSONField()

    class Meta:
        verbose_name = "منطقه ارسال"
        verbose_name_plural = "مناطق ارسال"

    def __str__(self):
        return self.name

class ShippingMethod(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True, blank=True)
    base_cost = models.DecimalField(max_digits=12, decimal_places=0)
    cost_per_kg = models.DecimalField(max_digits=8, decimal_places=0, default=0)
    free_above = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    min_days = models.PositiveSmallIntegerField(default=2)
    max_days = models.PositiveSmallIntegerField(default=7)
    zone = models.ForeignKey(ShippingZone, on_delete=models.CASCADE, null=True, blank=True, related_name="methods")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Shipping Method"
        verbose_name_plural = "Shipping Methods"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
