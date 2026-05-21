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
    \u0644\u06cc\u0633\u062a \u0645\u062d\u0635\u0648\u0644\u0627\u062a \u0641\u0639\u0627\u0644 \u0628\u0627 pagination \u0648 \u062c\u0633\u062a\u062c\u0648.

    - **page**: \u0634\u0645\u0627\u0631\u0647 \u0635\u0641\u062d\u0647 (\u067e\u06cc\u0634\u200c\u0641\u0631\u0636 \u06f1)
    - **page_size**: \u062a\u0639\u062f\u0627\u062f \u062f\u0631 \u0647\u0631 \u0635\u0641\u062d\u0647 (\u067e\u06cc\u0634\u200c\u0641\u0631\u0636 \u06f2\u06f0\u060c \u062d\u062f\u0627\u06a9\u062b\u0631 \u06f1\u06f0\u06f0)
    - **category_id**: \u0641\u06cc\u0644\u062a\u0631 \u0628\u0631 \u0627\u0633\u0627\u0633 \u062f\u0633\u062a\u0647\u200c\u0628\u0646\u062f\u06cc
    - **search**: \u062c\u0633\u062a\u062c\u0648 \u062f\u0631 \u0646\u0627\u0645 \u0648 \u062a\u0648\u0636\u06cc\u062d\u0627\u062a \u0645\u062d\u0635\u0648\u0644
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
        product = get_product_by_id(product_id)
        # Convert RelatedManager to list for Pydantic validation
        return ProductDetailOut(
            id=product.id,
            name=product.name,
            slug=product.slug,
            description=product.description,
            price=product.price,
            discount_price=product.discount_price,
            sku=product.sku,
            meta_title=product.meta_title,
            meta_description=product.meta_description,
            view_count=product.view_count,
            stock=product.stock,
            weight=product.weight,
            image=product.image.url if product.image else None,
            category=product.category,
            images=list(product.images.all()),
        )
    except NotFoundError:
        return JsonResponse(
            {"error": True, "code": "not_found", "message": "\u0645\u062d\u0635\u0648\u0644 \u06cc\u0627\u0641\u062a \u0646\u0634\u062f."},
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
            idempotency_key=payload.idempotency_key,
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

    return OrderOut(
        id=order.pk,
        status=order.status,
        total_price=order.total_price,
        shipping_cost=order.shipping_cost,
        payment_url=payment_url,
        items=order_items_out,
    )