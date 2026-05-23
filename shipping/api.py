from decimal import Decimal
from typing import List, Optional

from django.http import JsonResponse
from ninja import Router

from .schemas import (
    ShippingMethodOut,
    ShippingMethodDetailOut,
    ShippingOptionIn,
    ShippingOptionOut,
    CalculateShippingIn,
    ShippingOptionV2Out,
    CalculateShippingOut,
    ProvinceOut,
    CityOut,
    ShippingRateOut,
    ShippingRateCreateIn,
    ShippingRateUpdateIn,
)
from .services import (
    get_active_shipping_methods,
    calculate_shipping_options,
    calculate_shipping_cost_v2,
    calculate_shipping_options_v2,
    get_active_provinces,
    get_cities_by_province,
    get_shipping_rates_for_method,
    create_shipping_rate,
)
from core.auth import AdminBearer

router = Router(tags=["Shipping"])
_admin_auth = AdminBearer()


# ═════════════════════════════════════════════════════════════════════════════
# Public Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/methods",
    response=List[ShippingMethodOut],
    summary="لیست روش‌های ارسال فعال",
)
def list_shipping_methods(request):
    """لیست همه روش‌های ارسال فعال برای نمایش در صفحه checkout."""
    return get_active_shipping_methods()


@router.post(
    "/options",
    response=List[ShippingOptionOut],
    summary="محاسبه گزینه‌های ارسال بر اساس استان و سبد (legacy)",
)
def get_shipping_options(request, payload: ShippingOptionIn):
    """
    بر اساس نام استان مقصد و لیست آیتم‌های سبد، گزینه‌های ارسال با قیمت محاسبه‌شده
    برمی‌گرداند (نسخه قدیمی — با نام استان).
    """
    from store.models import Product

    total_weight_kg = 0.0
    order_total     = Decimal("0")

    for item in payload.items:
        product = (
            Product.objects
            .filter(pk=item.product_id, is_active=True)
            .only("weight", "price", "discount_price")
            .first()
        )
        if product is None:
            continue

        total_weight_kg += float(product.weight) * item.quantity
        effective_price  = product.discount_price if product.discount_price else product.price
        order_total     += effective_price * item.quantity

    return calculate_shipping_options(payload.province, total_weight_kg, order_total)


@router.get(
    "/provinces",
    response=List[ProvinceOut],
    summary="لیست استان‌ها",
)
def list_provinces(request):
    """لیست استان‌های فعال ایران."""
    return [
        ProvinceOut(id=p.id, name=p.name, code=p.code, is_active=p.is_active)
        for p in get_active_provinces()
    ]


@router.get(
    "/provinces/{province_id}/cities",
    response=List[CityOut],
    summary="لیست شهرهای یک استان",
)
def list_cities(request, province_id: int):
    """لیست شهرهای فعال یک استان."""
    return [
        CityOut(id=c.id, name=c.name, code=c.code, province_id=c.province_id, is_active=c.is_active)
        for c in get_cities_by_province(province_id)
    ]


@router.post(
    "/calculate",
    response=CalculateShippingOut,
    summary="محاسبه هزینه ارسال ( province + city + weight )",
)
def calculate_shipping(request, payload: CalculateShippingIn):
    """
    محاسبه هزینه ارسال بر اساس استان، شهر و وزن.
    خروجی شامل لیست روش‌های ارسال با قیمت و ETA است.
    """
    options = calculate_shipping_options_v2(
        province_id=payload.province_id,
        city_id=payload.city_id,
        total_weight_kg=payload.total_weight,
        order_total=payload.order_total,
    )

    return CalculateShippingOut(
        province_id=payload.province_id,
        city_id=payload.city_id,
        total_weight=payload.total_weight,
        order_total=payload.order_total,
        options=[
            ShippingOptionV2Out(
                id=opt["id"],
                name=opt["name"],
                slug=opt["slug"],
                carrier_name=opt["carrier_name"],
                tracking_url_template=opt["tracking_url_template"],
                cost=opt["cost"],
                min_days=opt["min_days"],
                max_days=opt["max_days"],
            )
            for opt in options
        ],
    )


# ═════════════════════════════════════════════════════════════════════════════
# Admin Endpoints
# ═════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/shipping-methods/",
    auth=_admin_auth,
    response=List[ShippingMethodDetailOut],
    summary="لیست کامل روش‌های ارسال (ادمین)",
)
def admin_list_shipping_methods(request):
    return [
        ShippingMethodDetailOut(
            id=m.id,
            name=m.name,
            slug=m.slug,
            carrier_name=m.carrier_name,
            tracking_url_template=m.tracking_url_template,
            base_cost=m.base_cost,
            cost_per_kg=m.cost_per_kg,
            free_above=m.free_above,
            min_days=m.min_days,
            max_days=m.max_days,
            is_active=m.is_active,
        )
        for m in ShippingMethod.objects.select_related("zone").all()
    ]


@router.get(
    "/admin/shipping-methods/{method_id}/rates/",
    auth=_admin_auth,
    response=List[ShippingRateOut],
    summary="لیست تعرفه‌های یک روش ارسال",
)
def admin_list_rates(request, method_id: int):
    return [
        ShippingRateOut(
            id=r.id,
            shipping_method_id=r.shipping_method_id,
            shipping_method_name=r.shipping_method.name,
            province_id=r.province_id,
            province_name=r.province.name,
            city_id=r.city_id,
            city_name=r.city.name if r.city else None,
            weight_min=r.weight_min,
            weight_max=r.weight_max,
            cost=r.cost,
            is_active=r.is_active,
        )
        for r in get_shipping_rates_for_method(method_id)
    ]


@router.post(
    "/admin/shipping-rates/",
    auth=_admin_auth,
    response=ShippingRateOut,
    summary="ایجاد تعرفه جدید",
)
def admin_create_rate(request, payload: ShippingRateCreateIn):
    from .models import ShippingMethod, Province, City

    try:
        method = ShippingMethod.objects.get(pk=payload.shipping_method_id)
    except ShippingMethod.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "روش ارسال یافت نشد."},
            status=404,
        )

    try:
        province = Province.objects.get(pk=payload.province_id)
    except Province.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "استان یافت نشد."},
            status=404,
        )

    city = None
    if payload.city_id:
        try:
            city = City.objects.get(pk=payload.city_id, province=province)
        except City.DoesNotExist:
            return JsonResponse(
                {"error": True, "code": "not_found", "message": "شهر یافت نشد."},
                status=404,
            )

    rate = ShippingRate.objects.create(
        shipping_method=method,
        province=province,
        city=city,
        weight_min=payload.weight_min,
        weight_max=payload.weight_max,
        cost=payload.cost,
    )

    return ShippingRateOut(
        id=rate.id,
        shipping_method_id=rate.shipping_method_id,
        shipping_method_name=rate.shipping_method.name,
        province_id=rate.province_id,
        province_name=rate.province.name,
        city_id=rate.city_id,
        city_name=rate.city.name if rate.city else None,
        weight_min=rate.weight_min,
        weight_max=rate.weight_max,
        cost=rate.cost,
        is_active=rate.is_active,
    )


@router.put(
    "/admin/shipping-rates/{rate_id}/",
    auth=_admin_auth,
    response=ShippingRateOut,
    summary="بروزرسانی تعرفه",
)
def admin_update_rate(request, rate_id: int, payload: ShippingRateUpdateIn):
    from .models import ShippingRate, City

    try:
        rate = ShippingRate.objects.select_related("province", "city", "shipping_method").get(pk=rate_id)
    except ShippingRate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "تعرفه یافت نشد."},
            status=404,
        )

    if payload.weight_min is not None:
        rate.weight_min = payload.weight_min
    if payload.weight_max is not None:
        rate.weight_max = payload.weight_max
    if payload.cost is not None:
        rate.cost = payload.cost
    if payload.is_active is not None:
        rate.is_active = payload.is_active
    if payload.city_id is not None:
        if payload.city_id == 0:
            rate.city = None
        else:
            try:
                rate.city = City.objects.get(pk=payload.city_id, province=rate.province)
            except City.DoesNotExist:
                return JsonResponse(
                    {"error": True, "code": "not_found", "message": "شهر یافت نشد."},
                    status=404,
                )

    rate.save()
    return ShippingRateOut(
        id=rate.id,
        shipping_method_id=rate.shipping_method_id,
        shipping_method_name=rate.shipping_method.name,
        province_id=rate.province_id,
        province_name=rate.province.name,
        city_id=rate.city_id,
        city_name=rate.city.name if rate.city else None,
        weight_min=rate.weight_min,
        weight_max=rate.weight_max,
        cost=rate.cost,
        is_active=rate.is_active,
    )


@router.delete(
    "/admin/shipping-rates/{rate_id}/",
    auth=_admin_auth,
    summary="حذف تعرفه",
)
def admin_delete_rate(request, rate_id: int):
    from .models import ShippingRate

    try:
        rate = ShippingRate.objects.get(pk=rate_id)
    except ShippingRate.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "تعرفه یافت نشد."},
            status=404,
        )
    rate.delete()
    return {"detail": "تعرفه با موفقیت حذف شد."}
