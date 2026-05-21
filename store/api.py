from typing import Optional

from django.http import JsonResponse
from ninja import Router

from core.auth import AuthBearer
from .schemas import (
    CategoryOut,
    PaginatedResponse,
    ProductDetailOut,
    ProductListOut,
    CreateOrderIn,
    OrderOut,
    OrderItemOut,
    STATUS_DISPLAY,
)
from .services import (
    get_active_categories,
    get_active_products,
    get_product_by_id,
    create_order,
)
from core.exceptions import NotFoundError, InsufficientStockError

router = Router(tags=["Store"])

_auth = AuthBearer()


@router.get("/categories", response=list[CategoryOut])
def list_categories(request):
    return get_active_categories()


@router.get("/products", response=PaginatedResponse[ProductListOut])
def list_products(
    request,
    page: int = 1,
    page_size: int = 20,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
):
    """
    لیست محصولات فعال با pagination و جستجو.

    - **page**: شماره صفحه (پیش‌فرض ۱)
    - **page_size**: تعداد در هر صفحه (پیش‌فرض ۲۰، حداکثر ۱۰۰)
    - **category_id**: فیلتر بر اساس دسته‌بندی
    - **search**: جستجو در نام و توضیحات محصول
    """
    data = get_active_products(
        category_id=category_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse[ProductListOut](
        count=data["count"],
        page=data["page"],
        page_size=data["page_size"],
        total_pages=data["total_pages"],
        results=[ProductListOut.model_validate(p) for p in data["results"]],
    )


@router.get("/products/{product_id}", response=ProductDetailOut)
def get_product(request, product_id: int):
    try:
        return get_product_by_id(product_id)
    except NotFoundError:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "محصول یافت نشد."},
            status=404,
        )


@router.post("/orders", response=OrderOut, auth=_auth)
def create_order_endpoint(request, payload: CreateOrderIn):
    items = [item.dict() for item in payload.items]
    try:
        result = create_order(
            user=request.auth,
            address_id=payload.address_id,
            shipping_method_id=payload.shipping_method_id,
            items=items,
        )
    except NotFoundError as e:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": str(e)},
            status=404,
        )
    except InsufficientStockError as e:
        return JsonResponse(
            {"error": True, "code": "insufficient_stock", "message": str(e)},
            status=400,
        )

    order = result["order"]
    payment_url = result.get("payment_url")

    order_items_out = [
        OrderItemOut(
            product_id=oi.product_id,
            product_name=oi.product_name_snapshot or oi.product.name,
            quantity=oi.quantity,
            unit_price=oi.unit_price,
        )
        for oi in order.items.select_related("product").all()
    ]

    # ست کردن status_display از STATUS_DISPLAY
    status_display = STATUS_DISPLAY.get(order.status, order.status)

    return OrderOut(
        id=order.pk,
        status=order.status,
        status_display=status_display,
        total_price=order.total_price,
        shipping_cost=order.shipping_cost,
        payment_url=payment_url,
        items=order_items_out,
    )
