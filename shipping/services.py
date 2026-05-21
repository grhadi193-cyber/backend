from decimal import Decimal
from typing import List, Optional

from core.exceptions import NotFoundError
from .models import ShippingMethod, ShippingZone


# ── Catalogue ─────────────────────────────────────────────────────────────────

def get_active_shipping_methods() -> List[ShippingMethod]:
    """لیست همه روش‌های ارسال فعال مرتب‌شده بر اساس نام."""
    return list(ShippingMethod.objects.select_related("zone").filter(is_active=True))


# ── Zone lookup ───────────────────────────────────────────────────────────────

def _find_zone_for_province(province: str) -> Optional[ShippingZone]:
    """
    Zone متناسب با نام استان را پیدا می‌کند.
    مقایسه case-sensitive روی JSONField (آرایه‌ای از رشته فارسی).
    اگر استان در هیچ zone‌ای نبود → None برمی‌گرداند.
    """
    return ShippingZone.objects.filter(provinces__contains=province).first()


# ── Cost calculator ───────────────────────────────────────────────────────────

def _calc_cost(
    method: ShippingMethod,
    total_weight_kg: float,
    order_total: Decimal,
) -> Decimal:
    """
    هزینه ارسال برای یک متد مشخص محاسبه می‌کند.

    منطق:
      - اگر free_above تنظیم شده و order_total >= free_above → cost = 0
      - وزن اضافه از ۱ کیلو: extra_weight = max(0, weight - 1)
      - cost = base_cost + extra_weight × cost_per_kg
    """
    if method.free_above is not None and order_total >= method.free_above:
        return Decimal("0")

    extra_weight = max(0.0, total_weight_kg - 1.0)
    cost = method.base_cost + Decimal(str(extra_weight)) * method.cost_per_kg
    return cost


# ── Public API ────────────────────────────────────────────────────────────────

def calculate_shipping_options(
    province: str,
    total_weight_kg: float,
    order_total: Decimal,
) -> list:
    """
    بر اساس استان مقصد و وزن سبد، لیست روش‌های ارسال با قیمت برمی‌گرداند.

    منطق انتخاب متدها:
      1. zone متناسب با province پیدا می‌شود.
      2. اگر zone پیدا شد → متدهای آن zone برگردانده می‌شوند.
      3. اگر zone پیدا نشد (استان در هیچ منطقه‌ای نیست) →
         متدهای بدون zone (zone=None) که universal هستند برگردانده می‌شوند.
         این رفتار «fallback» از بین رفتن تمام گزینه‌های ارسال را جلوگیری می‌کند.

    خروجی: لیستی از dict با کلیدهای id, name, cost, min_days, max_days
    """
    zone = _find_zone_for_province(province)

    if zone is not None:
        methods = ShippingMethod.objects.filter(zone=zone, is_active=True)
    else:
        # استان در هیچ zone‌ای ثبت نشده → متدهای universal (zone=None)
        methods = ShippingMethod.objects.filter(zone__isnull=True, is_active=True)

    results = []
    for method in methods.order_by("base_cost"):
        cost = _calc_cost(method, total_weight_kg, order_total)
        results.append({
            "id":       method.pk,
            "name":     method.name,
            "cost":     cost,
            "min_days": method.min_days,
            "max_days": method.max_days,
        })

    return results


def calculate_shipping_cost(
    method_id_or_obj,
    total_weight: Optional[float] = None,
    order_total: Optional[Decimal] = None,
) -> Decimal:
    """
    هزینه ارسال برای یک ShippingMethod مشخص محاسبه می‌کند.
    هم method_id (int) و هم instance (ShippingMethod) را قبول می‌کند.

    این تابع توسط store/services.py هنگام ایجاد سفارش فراخوانی می‌شود.
    اگر total_weight یا order_total ارائه نشده باشد با مقادیر پیش‌فرض کار می‌کند.
    """
    if isinstance(method_id_or_obj, ShippingMethod):
        method = method_id_or_obj
    else:
        try:
            method = ShippingMethod.objects.get(pk=method_id_or_obj, is_active=True)
        except ShippingMethod.DoesNotExist:
            raise NotFoundError(
                f"ShippingMethod با id={method_id_or_obj} یافت نشد یا غیرفعال است."
            )

    weight = total_weight if total_weight is not None else 0.0
    total  = order_total  if order_total  is not None else Decimal("0")

    return _calc_cost(method, weight, total)
