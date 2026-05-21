"""
Admin Panel API  —  Phase 17 + 18 + 19 + Fixes
================================================
تمام endpoint‌ها نیاز به is_staff=True دارند (AdminBearer).

Routers:
  GET  /api/admin/dashboard
  GET  /api/admin/users/
  GET  /api/admin/users/{id}/
  PUT  /api/admin/users/{id}/
  GET  /api/admin/orders/
  GET  /api/admin/orders/{id}/
  PUT  /api/admin/orders/{id}/status/
  GET  /api/admin/products/
  POST /api/admin/products/
  GET  /api/admin/products/{id}/
  PUT  /api/admin/products/{id}/
  PUT  /api/admin/products/{id}/stock/
  DELETE /api/admin/products/{id}/
  GET  /api/admin/analytics/overview/
  GET  /api/admin/settings/
  PUT  /api/admin/settings/

Phase 19: total_pages به AdminUserListOut و AdminOrderListOut اضافه شد.
Fixes:  بررسی تکراری بودن slug در ایجاد و ویرایش محصول.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from django.db import transaction as db_transaction
from django.db.models import Count, F, Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from accounts.models import User
from core.auth import AdminBearer
from core.exceptions import AppException, NotFoundError
from store.models import Order, OrderStatusHistory, Product
from store.schemas import UserOrderOut

logger = logging.getLogger(__name__)

router = Router(tags=["Admin"])

_auth = AdminBearer()


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class DashboardOut(BaseModel):
    total_users: int
    total_orders: int
    total_revenue: int
    orders_today: int
    orders_this_week: int
    orders_this_month: int


class AdminUserOut(BaseModel):
    id: int
    phone_number: str
    full_name: str
    email: Optional[str] = None
    is_active: bool
    date_joined: datetime
    order_count: int

    model_config = {"from_attributes": True}


class AdminUserListOut(BaseModel):
    count: int
    page: int
    page_size: int
    total_pages: int
    results: List[AdminUserOut]


class AdminUserUpdateIn(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class AdminOrderListOut(BaseModel):
    count: int
    page: int
    page_size: int
    total_pages: int
    results: List[UserOrderOut]


class AdminOrderStatusIn(BaseModel):
    status: str
    note: str = ""
    tracking_number: str = ""
    postal_tracking: str = ""


class AdminProductIn(BaseModel):
    name: str
    slug: str
    description: str = ""
    price: Decimal
    discount_price: Optional[Decimal] = None
    stock: int = 0
    weight: Decimal = Decimal("0")
    category_id: Optional[int] = None
    sku: Optional[str] = None
    meta_title: str = ""
    meta_description: str = ""
    is_active: bool = True


class AdminProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: Decimal
    discount_price: Optional[Decimal] = None
    stock: int
    weight: Decimal
    category_id: Optional[int] = None
    sku: Optional[str] = None
    meta_title: str
    meta_description: str
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AdminProductListOut(BaseModel):
    count: int
    page: int
    page_size: int
    total_pages: int
    results: List[AdminProductOut]


class AdminStockUpdateIn(BaseModel):
    quantity_delta: int


class TopProductItem(BaseModel):
    id: int
    name: str
    total_sold: int
    revenue: Decimal


class AnalyticsOut(BaseModel):
    revenue_today: Decimal
    revenue_this_week: Decimal
    revenue_this_month: Decimal
    orders_by_status: dict
    top_products: List[TopProductItem]


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────

def _paginate(qs, page: int, page_size: int):
    """
    صفحه‌بندی روی QuerySet.
    برمی‌گرداند: (total_count, total_pages, page_qs)
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    total = qs.count()
    start = (page - 1) * page_size
    total_pages = max(1, (total + page_size - 1) // page_size)
    return total, total_pages, qs[start: start + page_size]


def _revenue_for(qs):
    """مجموع total_price برای سفارش‌های paid از یک QuerySet."""
    agg = qs.filter(status="paid").aggregate(total=Sum("total_price"))
    return agg["total"] or Decimal("0")


def _check_duplicate_slug(slug: str, exclude_id: Optional[int] = None):
    """
    بررسی تکراری بودن slug.
    اگر exclude_id داده شود، آن محصول از چک مستثنی می‌شود (برای ویرایش).
    """
    qs = Product.objects.filter(slug=slug)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return qs.exists()


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard",
    auth=_auth,
    response=DashboardOut,
    summary="داشبورد ادمین",
)
def admin_dashboard(request):
    """آمار کلی سایت."""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    total_users = User.objects.count()
    total_orders = Order.objects.count()
    revenue_agg = Order.objects.filter(status="paid").aggregate(total=Sum("total_price"))
    total_revenue = int(revenue_agg["total"] or 0)

    orders_today = Order.objects.filter(created_at__gte=today_start).count()
    orders_this_week = Order.objects.filter(created_at__gte=week_start).count()
    orders_this_month = Order.objects.filter(created_at__gte=month_start).count()

    return DashboardOut(
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
        orders_today=orders_today,
        orders_this_week=orders_this_week,
        orders_this_month=orders_this_month,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/users/",
    auth=_auth,
    response=AdminUserListOut,
    summary="لیست کاربران (ادمین)",
)
def admin_list_users(request, page: int = 1, page_size: int = 20, search: str = ""):
    qs = User.objects.annotate(order_count=Count("orders")).order_by("-date_joined")
    if search:
        qs = qs.filter(
            Q(phone_number__icontains=search) | Q(full_name__icontains=search)
        )

    total, total_pages, page_qs = _paginate(qs, page, page_size)

    results = [
        AdminUserOut(
            id=u.pk,
            phone_number=u.phone_number,
            full_name=u.full_name,
            email=u.email,
            is_active=u.is_active,
            date_joined=u.date_joined,
            order_count=u.order_count,
        )
        for u in page_qs
    ]
    return AdminUserListOut(
        count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


@router.get(
    "/users/{user_id}/",
    auth=_auth,
    response=AdminUserOut,
    summary="جزئیات کاربر (ادمین)",
)
def admin_get_user(request, user_id: int):
    try:
        user = User.objects.annotate(order_count=Count("orders")).get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "کاربر یافت نشد."},
            status=404,
        )
    return AdminUserOut(
        id=user.pk,
        phone_number=user.phone_number,
        full_name=user.full_name,
        email=user.email,
        is_active=user.is_active,
        date_joined=user.date_joined,
        order_count=user.order_count,
    )


@router.put(
    "/users/{user_id}/",
    auth=_auth,
    summary="ویرایش کاربر (ادمین)",
)
def admin_update_user(request, user_id: int, payload: AdminUserUpdateIn):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "کاربر یافت نشد."},
            status=404,
        )

    update_fields = []
    if payload.full_name is not None:
        user.full_name = payload.full_name
        update_fields.append("full_name")
    if payload.is_active is not None:
        user.is_active = payload.is_active
        update_fields.append("is_active")

    if update_fields:
        user.save(update_fields=update_fields)

    return {"detail": "کاربر با موفقیت ویرایش شد."}


# ─────────────────────────────────────────────────────────────────────────────
# Orders
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/orders/",
    auth=_auth,
    response=AdminOrderListOut,
    summary="لیست سفارش‌ها (ادمین)",
)
def admin_list_orders(request, page: int = 1, page_size: int = 20, status: str = ""):
    qs = (
        Order.objects.all()
        .prefetch_related("items__product", "history")
        .order_by("-created_at")
    )
    if status:
        qs = qs.filter(status=status)

    total, total_pages, page_qs = _paginate(qs, page, page_size)

    results = [UserOrderOut.model_validate(o) for o in page_qs]
    return AdminOrderListOut(
        count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


@router.get(
    "/orders/{order_id}/",
    auth=_auth,
    response=UserOrderOut,
    summary="جزئیات سفارش (ادمین)",
)
def admin_get_order(request, order_id: int):
    try:
        order = (
            Order.objects
            .prefetch_related("items__product", "history")
            .get(pk=order_id)
        )
    except Order.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "سفارش یافت نشد."},
            status=404,
        )
    return UserOrderOut.model_validate(order)


@router.put(
    "/orders/{order_id}/status/",
    auth=_auth,
    summary="تغییر وضعیت سفارش (ادمین)",
)
def admin_update_order_status(request, order_id: int, payload: AdminOrderStatusIn):
    from store.services import update_order_status
    try:
        order = update_order_status(
            order_id=order_id,
            new_status=payload.status,
            admin_user=request.auth,
            tracking_number=payload.tracking_number,
            postal_tracking=payload.postal_tracking,
            note=payload.note,
        )
    except AppException as exc:
        return JsonResponse(
            {"error": True, "code": "validation_error", "message": exc.message},
            status=exc.status_code or 400,
        )
    return UserOrderOut.model_validate(order)


# ─────────────────────────────────────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/products/",
    auth=_auth,
    response=AdminProductListOut,
    summary="لیست محصولات (ادمین)",
)
def admin_list_products(request, page: int = 1, page_size: int = 20, search: str = ""):
    qs = Product.objects.all().select_related("category").order_by("-created_at")
    if search:
        qs = qs.filter(
            Q(name__icontains=search) | Q(slug__icontains=search)
        )

    total, total_pages, page_qs = _paginate(qs, page, page_size)

    results = [AdminProductOut.model_validate(p) for p in page_qs]
    return AdminProductListOut(
        count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        results=results,
    )


@router.post(
    "/products/",
    auth=_auth,
    response=AdminProductOut,
    summary="ایجاد محصول جدید (ادمین)",
)
def admin_create_product(request, payload: AdminProductIn):
    from store.models import Category

    # ── بررسی تکراری بودن slug ──
    if _check_duplicate_slug(payload.slug):
        return JsonResponse(
            {
                "error": True,
                "code": "duplicate_slug",
                "message": f"اسلاگ '{payload.slug}' قبلاً استفاده شده است. لطفاً اسلاگ دیگری انتخاب کنید.",
            },
            status=400,
        )

    # ── بررسی تکراری بودن sku (اگر داده شده) ──
    if payload.sku and Product.objects.filter(sku=payload.sku).exists():
        return JsonResponse(
            {
                "error": True,
                "code": "duplicate_sku",
                "message": f"SKU '{payload.sku}' قبلاً استفاده شده است.",
            },
            status=400,
        )

    category = None
    if payload.category_id:
        try:
            category = Category.objects.get(pk=payload.category_id)
        except Category.DoesNotExist:
            return JsonResponse(
                {"error": True, "code": "not_found", "message": "دسته‌بندی یافت نشد."},
                status=404,
            )

    product = Product.objects.create(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        price=payload.price,
        discount_price=payload.discount_price,
        stock=payload.stock,
        weight=payload.weight,
        category=category,
        sku=payload.sku or None,
        meta_title=payload.meta_title,
        meta_description=payload.meta_description,
        is_active=payload.is_active,
    )
    return AdminProductOut.model_validate(product)


@router.get(
    "/products/{product_id}/",
    auth=_auth,
    response=AdminProductOut,
    summary="جزئیات محصول (ادمین)",
)
def admin_get_product(request, product_id: int):
    try:
        product = Product.objects.select_related("category").get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "محصول یافت نشد."},
            status=404,
        )
    return AdminProductOut.model_validate(product)


@router.put(
    "/products/{product_id}/",
    auth=_auth,
    response=AdminProductOut,
    summary="ویرایش محصول (ادمین)",
)
def admin_update_product(request, product_id: int, payload: AdminProductIn):
    from store.models import Category
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "محصول یافت نشد."},
            status=404,
        )

    # ── بررسی تکراری بودن slug (محصول فعلی مستثنی) ──
    if _check_duplicate_slug(payload.slug, exclude_id=product_id):
        return JsonResponse(
            {
                "error": True,
                "code": "duplicate_slug",
                "message": f"اسلاگ '{payload.slug}' قبلاً استفاده شده است. لطفاً اسلاگ دیگری انتخاب کنید.",
            },
            status=400,
        )

    # ── بررسی تکراری بودن sku (محصول فعلی مستثنی) ──
    if payload.sku and Product.objects.filter(sku=payload.sku).exclude(pk=product_id).exists():
        return JsonResponse(
            {
                "error": True,
                "code": "duplicate_sku",
                "message": f"SKU '{payload.sku}' قبلاً استفاده شده است.",
            },
            status=400,
        )

    category = None
    if payload.category_id:
        try:
            category = Category.objects.get(pk=payload.category_id)
        except Category.DoesNotExist:
            return JsonResponse(
                {"error": True, "code": "not_found", "message": "دسته‌بندی یافت نشد."},
                status=404,
            )

    product.name = payload.name
    product.slug = payload.slug
    product.description = payload.description
    product.price = payload.price
    product.discount_price = payload.discount_price
    product.stock = payload.stock
    product.weight = payload.weight
    product.category = category
    product.sku = payload.sku or None
    product.meta_title = payload.meta_title
    product.meta_description = payload.meta_description
    product.is_active = payload.is_active
    product.save()

    return AdminProductOut.model_validate(product)


@router.put(
    "/products/{product_id}/stock/",
    auth=_auth,
    summary="تغییر موجودی محصول (ادمین)",
)
def admin_update_stock(request, product_id: int, payload: AdminStockUpdateIn):
    try:
        with db_transaction.atomic():
            product = Product.objects.select_for_update().get(pk=product_id)
            new_stock = product.stock + payload.quantity_delta
            if new_stock < 0:
                return JsonResponse(
                    {
                        "error": True,
                        "code": "insufficient_stock",
                        "message": f"موجودی کافی نیست. موجودی فعلی: {product.stock}",
                    },
                    status=400,
                )
            product.stock = new_stock
            product.save(update_fields=["stock"])
    except Product.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "محصول یافت نشد."},
            status=404,
        )

    return {"detail": "موجودی با موفقیت بروزرسانی شد.", "new_stock": product.stock}


@router.delete(
    "/products/{product_id}/",
    auth=_auth,
    summary="غیرفعال کردن محصول (ادمین)",
)
def admin_delete_product(request, product_id: int):
    """
    soft delete: محصول را غیرفعال می‌کند (is_active=False).
    محصول از دیتابیس حذف نمی‌شود.
    """
    try:
        product = Product.objects.get(pk=product_id)
    except Product.DoesNotExist:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "محصول یافت نشد."},
            status=404,
        )
    product.is_active = False
    product.save(update_fields=["is_active"])
    return {"detail": "محصول با موفقیت غیرفعال شد."}


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/analytics/overview/",
    auth=_auth,
    response=AnalyticsOut,
    summary="آنالیتیکس فروش (ادمین)",
)
def admin_analytics_overview(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    revenue_today = _revenue_for(Order.objects.filter(created_at__gte=today_start))
    revenue_this_week = _revenue_for(Order.objects.filter(created_at__gte=week_start))
    revenue_this_month = _revenue_for(Order.objects.filter(created_at__gte=month_start))

    status_counts = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
    )
    all_statuses = [s for s, _ in Order.STATUS_CHOICES]
    status_map = {row["status"]: row["count"] for row in status_counts}
    orders_by_status = {s: status_map.get(s, 0) for s in all_statuses}

    from store.models import OrderItem
    top_items = (
        OrderItem.objects.filter(order__status="paid")
        .values("product_id", "product__name")
        .annotate(
            total_sold=Sum("quantity"),
            revenue=Sum(F("quantity") * F("unit_price")),
        )
        .order_by("-total_sold")[:5]
    )

    top_products = [
        TopProductItem(
            id=row["product_id"],
            name=row["product__name"],
            total_sold=row["total_sold"],
            revenue=row["revenue"] or Decimal("0"),
        )
        for row in top_items
    ]

    return AnalyticsOut(
        revenue_today=revenue_today,
        revenue_this_week=revenue_this_week,
        revenue_this_month=revenue_this_month,
        orders_by_status=orders_by_status,
        top_products=top_products,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SiteSettings  (Phase 18)
# ─────────────────────────────────────────────────────────────────────────────

class AdminSiteSettingsOut(BaseModel):
    site_name:        str
    banner_text:      str
    announcement:     str
    primary_color:    str
    maintenance_mode: bool
    social_instagram: str
    social_telegram:  str
    support_phone:    str
    logo:             Optional[str] = None
    hero_title:       str
    hero_text:        str
    hero_banner:      Optional[str] = None
    about_us:         str

    model_config = {"from_attributes": True}


class AdminSiteSettingsUpdateIn(BaseModel):
    site_name:        Optional[str]  = None
    banner_text:      Optional[str]  = None
    announcement:     Optional[str]  = None
    primary_color:    Optional[str]  = None
    maintenance_mode: Optional[bool] = None
    social_instagram: Optional[str]  = None
    social_telegram:  Optional[str]  = None
    support_phone:    Optional[str]  = None
    hero_title:       Optional[str]  = None
    hero_text:        Optional[str]  = None
    about_us:         Optional[str]  = None


def _settings_to_out(s, request) -> AdminSiteSettingsOut:
    def _url(field):
        if field and hasattr(field, "url"):
            try:
                return request.build_absolute_uri(field.url)
            except Exception:
                return None
        return None

    return AdminSiteSettingsOut(
        site_name        = s.site_name,
        banner_text      = s.banner_text,
        announcement     = s.announcement,
        primary_color    = s.primary_color,
        maintenance_mode = s.maintenance_mode,
        social_instagram = s.social_instagram,
        social_telegram  = s.social_telegram,
        support_phone    = s.support_phone,
        logo             = _url(s.logo),
        hero_title       = s.hero_title,
        hero_text        = s.hero_text,
        hero_banner      = _url(s.hero_banner),
        about_us         = s.about_us,
    )


@router.get(
    "/settings/",
    auth=_auth,
    response=AdminSiteSettingsOut,
    summary="دریافت تنظیمات سایت (ادمین)",
)
def admin_get_settings(request):
    from core.models import SiteSettings
    return _settings_to_out(SiteSettings.get(), request)


@router.put(
    "/settings/",
    auth=_auth,
    response=AdminSiteSettingsOut,
    summary="بروزرسانی تنظیمات سایت (ادمین)",
)
def admin_update_settings(request, payload: AdminSiteSettingsUpdateIn):
    """
    هر فیلدی که در body ارسال شود (غیر از None) آپدیت می‌شود.
    فیلدهای ارسال‌نشده یا None تغییر نمی‌کنند.
    آپلود لوگو/بنر از این endpoint پشتیبانی نمی‌شود — از /admin Django بارگذاری کنید.
    """
    from core.models import SiteSettings
    s = SiteSettings.get()

    updatable_fields = [
        "site_name", "banner_text", "announcement", "primary_color",
        "maintenance_mode", "social_instagram", "social_telegram",
        "support_phone", "hero_title", "hero_text", "about_us",
    ]
    update_fields = []
    for field in updatable_fields:
        value = getattr(payload, field, None)
        if value is not None:
            setattr(s, field, value)
            update_fields.append(field)

    if update_fields:
        s.save(update_fields=update_fields)

    return _settings_to_out(s, request)
