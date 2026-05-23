from decimal import Decimal
from typing import List, Optional

from core.exceptions import NotFoundError
from .models import (
    ShippingMethod,
    ShippingRate,
    ShippingZone,
    Province,
    City,
)


# ── Province / City ─────────────────────────────────────────────────────────

def get_active_provinces() -> List[Province]:
    """لیست استان‌های فعال."""
    return list(Province.objects.filter(is_active=True).order_by("name"))


def get_cities_by_province(province_id: int) -> List[City]:
    """لیست شهرهای یک استان."""
    return list(City.objects.filter(province_id=province_id, is_active=True).order_by("name"))


# ── Shipping Methods ────────────────────────────────────────────────────────

def get_active_shipping_methods() -> List[ShippingMethod]:
    """لیست همه روش‌های ارسال فعال مرتب‌شده بر اساس نام."""
    return list(ShippingMethod.objects.select_related("zone").filter(is_active=True))


# ── Zone lookup ─────────────────────────────────────────────────────────────

def _find_zone_for_province(province_name: str) -> Optional[ShippingZone]:
    """
    Zone متناسب با نام استان را پیدا می‌کند.
    مقایسه case-sensitive روی JSONField (آرایه‌ای از رشته فارسی).
    اگر استان در هیچ zone‌ای نبود → None برمی‌گرداند.
    """
    return ShippingZone.objects.filter(provinces__contains=province_name).first()


# ── Cost calculator (legacy — base cost only) ──────────────────────────────

def _calc_base_cost(
    method: ShippingMethod,
    total_weight_kg: float,
    order_total: Decimal,
) -> Decimal:
    """
    هزینه ارسال پایه برای یک متد مشخص محاسبه می‌کند.

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


# ── Advanced Cost calculator (province + city + weight) ────────────────────

def calculate_shipping_cost_v2(
    shipping_method_id: int,
    province_id: int,
    city_id: Optional[int],
    total_weight_kg: float,
    order_total: Optional[Decimal] = None,
) -> Decimal:
    """
    محاسبه هزینه ارسال بر اساس روش، استان، شهر و وزن.
    ابتدا ShippingRate را چک می‌کند، اگر نبود از base_cost استفاده می‌کند.
    """
    try:
        method = ShippingMethod.objects.get(pk=shipping_method_id, is_active=True)
    except ShippingMethod.DoesNotExist:
        raise NotFoundError(f"ShippingMethod با id={shipping_method_id} یافت نشد یا غیرفعال است.")

    try:
        province = Province.objects.get(pk=province_id, is_active=True)
    except Province.DoesNotExist:
        raise NotFoundError(f"استان با id={province_id} یافت نشد.")

    city = None
    if city_id:
        try:
            city = City.objects.get(pk=city_id, province=province, is_active=True)
        except City.DoesNotExist:
            pass  # اگر شهر پیدا نشد، نرخ استانی را استفاده می‌کنیم

    # 1. چک کردن free_above
    if method.free_above is not None and order_total is not None and order_total >= method.free_above:
        return Decimal("0")

    # 2. جستجوی ShippingRate
    rate_qs = ShippingRate.objects.filter(
        shipping_method=method,
        province=province,
        is_active=True,
    )

    if city:
        # ابتدا نرخ شهر را چک کن
        city_rate = rate_qs.filter(city=city, weight_min__lte=total_weight_kg, weight_max__gte=total_weight_kg).first()
        if city_rate:
            return city_rate.cost

    # نرخ استان (city=None)
    province_rate = rate_qs.filter(
        city__isnull=True,
        weight_min__lte=total_weight_kg,
        weight_max__gte=total_weight_kg,
    ).first()
    if province_rate:
        return province_rate.cost

    # 3. fallback به base_cost
    return _calc_base_cost(method, total_weight_kg, order_total or Decimal("0"))


def calculate_shipping_options_v2(
    province_id: int,
    city_id: Optional[int],
    total_weight_kg: float,
    order_total: Decimal,
) -> list:
    """
    بر اساس استان، شهر (اختیاری) و وزن سبد، لیست روش‌های ارسال با قیمت محاسبه‌شده برمی‌گرداند.
    """
    try:
        province = Province.objects.get(pk=province_id, is_active=True)
    except Province.DoesNotExist:
        return []

    methods = ShippingMethod.objects.filter(is_active=True)

    results = []
    for method in methods:
        try:
            cost = calculate_shipping_cost_v2(
                shipping_method_id=method.pk,
                province_id=province_id,
                city_id=city_id,
                total_weight_kg=total_weight_kg,
                order_total=order_total,
            )
            results.append({
                "id": method.pk,
                "name": method.name,
                "slug": method.slug,
                "carrier_name": method.carrier_name,
                "tracking_url_template": method.tracking_url_template,
                "cost": cost,
                "min_days": method.min_days,
                "max_days": method.max_days,
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["cost"])


# ── Legacy: Public API (backward compatible) ───────────────────────────────

def calculate_shipping_options(
    province: str,
    total_weight_kg: float,
    order_total: Decimal,
) -> list:
    """
    بر اساس نام استان (legacy) و وزن سبد، لیست روش‌های ارسال با قیمت برمی‌گرداند.
    این تابع برای سازگاری با کد قدیمی نگه داشته شده است.
    """
    zone = _find_zone_for_province(province)

    if zone is not None:
        methods = ShippingMethod.objects.filter(zone=zone, is_active=True)
    else:
        methods = ShippingMethod.objects.filter(zone__isnull=True, is_active=True)

    results = []
    for method in methods.order_by("base_cost"):
        cost = _calc_base_cost(method, total_weight_kg, order_total)
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

    return _calc_base_cost(method, weight, total)


# ── Rate CRUD helpers ──────────────────────────────────────────────────────

def get_shipping_rates_for_method(method_id: int) -> List[ShippingRate]:
    """لیست تعرفه‌های یک روش ارسال."""
    return list(
        ShippingRate.objects
        .filter(shipping_method_id=method_id)
        .select_related("province", "city", "shipping_method")
        .order_by("province__name", "city__name", "weight_min")
    )


def create_shipping_rate(
    shipping_method_id: int,
    province_id: int,
    city_id: Optional[int],
    weight_min: Decimal,
    weight_max: Decimal,
    cost: Decimal,
) -> ShippingRate:
    method = ShippingMethod.objects.get(pk=shipping_method_id)
    province = Province.objects.get(pk=province_id)
    city = City.objects.get(pk=city_id) if city_id else None

    return ShippingRate.objects.create(
        shipping_method=method,
        province=province,
        city=city,
        weight_min=weight_min,
        weight_max=weight_max,
        cost=cost,
    )
