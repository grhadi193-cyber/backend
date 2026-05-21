from decimal import Decimal
from typing import List

from ninja import Router

from .schemas import ShippingMethodOut, ShippingOptionIn, ShippingOptionOut
from .services import get_active_shipping_methods, calculate_shipping_options

router = Router(tags=["Shipping"])


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
    summary="محاسبه گزینه‌های ارسال بر اساس استان و سبد",
)
def get_shipping_options(request, payload: ShippingOptionIn):
    """
    بر اساس استان مقصد و لیست آیتم‌های سبد، گزینه‌های ارسال با قیمت محاسبه‌شده
    برمی‌گرداند.

    - وزن کل از مجموع وزن × تعداد هر محصول محاسبه می‌شود.
    - مبلغ کل از قیمت مؤثر (discount_price اگر موجود بود، وگرنه price) محاسبه می‌شود.
    - اگر استان در هیچ zone‌ای نباشد، متدهای universal (zone=None) نمایش داده می‌شوند.
    - محصولات ناموجود یا غیرفعال نادیده گرفته می‌شوند.
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
            continue  # محصول ناموجود یا غیرفعال → نادیده گرفته می‌شود

        total_weight_kg += float(product.weight) * item.quantity
        effective_price  = product.discount_price if product.discount_price else product.price
        order_total     += effective_price * item.quantity

    return calculate_shipping_options(payload.province, total_weight_kg, order_total)
