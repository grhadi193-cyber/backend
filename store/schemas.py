from decimal import Decimal
from typing import Generic, List, Optional, TypeVar
from datetime import datetime
from pydantic import BaseModel, computed_field, ConfigDict, field_validator


# ── Generic Paginated Response ─────────────────────────────────────────────

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """پاسخ صفحه‌بندی‌شده عمومی — قابل استفاده برای هر نوع داده."""
    count: int
    page: int
    page_size: int
    total_pages: int
    results: List[T]


# ── Category ─────────────────────────────────────────────────────────────────

class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True)


# ── Product Images ────────────────────────────────────────────────────────────

class ProductImageOut(BaseModel):
    id: int
    image: str
    alt_text: str
    order: int
    is_cover: bool

    model_config = ConfigDict(from_attributes=True)


# ── Product List (public) ─────────────────────────────────────────────────────

class ProductListOut(BaseModel):
    id: int
    name: str
    slug: str
    price: Decimal
    discount_price: Optional[Decimal] = None
    weight: Decimal = Decimal("0")
    stock: int
    image: Optional[str] = None
    category: Optional[CategoryOut] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator('image', mode='before')
    @classmethod
    def convert_image_to_str(cls, v):
        """تبدیل ImageFieldFile به رشته یا None"""
        if v is None or v == '':
            return None
        if hasattr(v, 'url'):
            return v.url
        return str(v)

    @computed_field
    @property
    def effective_price(self) -> Decimal:
        """The price the customer actually pays — discount_price if set, else price."""
        return self.discount_price if self.discount_price is not None else self.price

    @computed_field
    @property
    def is_on_sale(self) -> bool:
        """True when a discount is actively applied."""
        return self.discount_price is not None and self.discount_price < self.price


# ── Product Detail (public) ───────────────────────────────────────────────────

class ProductDetailOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: Decimal
    discount_price: Optional[Decimal] = None
    sku: Optional[str] = None
    meta_title: str = ""
    meta_description: str = ""
    view_count: int = 0
    stock: int
    weight: Decimal
    image: Optional[str] = None
    category: Optional[CategoryOut] = None
    images: List[ProductImageOut] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator('image', mode='before')
    @classmethod
    def convert_image_to_str(cls, v):
        """تبدیل ImageFieldFile به رشته یا None"""
        if v is None or v == '':
            return None
        if hasattr(v, 'url'):
            return v.url
        return str(v)

    @field_validator('images', mode='before')
    @classmethod
    def convert_images_to_list(cls, v):
        """تبدیل RelatedManager به لیست"""
        if hasattr(v, 'all'):
            return list(v.all())
        return v if isinstance(v, list) else []

    @computed_field
    @property
    def effective_price(self) -> Decimal:
        """The price the customer actually pays."""
        return self.discount_price if self.discount_price is not None else self.price

    @computed_field
    @property
    def is_on_sale(self) -> bool:
        return self.discount_price is not None and self.discount_price < self.price


# ── Order (Create) ────────────────────────────────────────────────────────────

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int


class CreateOrderIn(BaseModel):
    address_id: int
    shipping_method_id: int
    items: List[OrderItemIn]
    idempotency_key: str = ""


# ── Order (Response) ──────────────────────────────────────────────────────────

_STATUS_DISPLAY_MAP = {
    "pending":    "درحال تایید",
    "paid":       "تایید شده",
    "processing": "آماده سازی",
    "shipped":    "تحویل به پست",
    "delivered":  "تحویل شده",
    "cancelled":  "لغو شده",
}


class OrderItemOut(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    status: str
    total_price: Decimal
    shipping_cost: Decimal
    tracking_number: str = ""
    payment_url: Optional[str] = None
    items: List[OrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def status_display(self) -> str:
        """نام فارسی وضعیت سفارش — از روی مقدار status محاسبه می‌شود."""
        return _STATUS_DISPLAY_MAP.get(self.status, self.status)


# ── Order Tracking ────────────────────────────────────────────────────────────

# نگه‌داشته می‌شود برای سازگاری با بقیه کدهای موجود
STATUS_DISPLAY = _STATUS_DISPLAY_MAP


class OrderItemTrackingOut(BaseModel):
    product_name: str
    quantity: int
    unit_price: Decimal


class OrderStatusHistoryOut(BaseModel):
    status: str
    status_display: str
    note: str
    created_at: datetime


class UserOrderOut(BaseModel):
    id: int
    tracking_number: str
    postal_tracking: str
    carrier_name: str
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    customer_notes: str
    status: str
    status_display: str
    total_price: Decimal
    shipping_cost: Decimal
    created_at: datetime
    shipping_address_snapshot: Optional[dict] = None
    items: List[OrderItemTrackingOut]
    history: List[OrderStatusHistoryOut] = []

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        items = [
            OrderItemTrackingOut(
                product_name=i.product_name_snapshot or i.product.name,
                quantity=i.quantity,
                unit_price=i.unit_price,
            )
            for i in obj.items.all()
        ]
        history = [
            OrderStatusHistoryOut(
                status=h.status,
                status_display=_STATUS_DISPLAY_MAP.get(h.status, h.status),
                note=h.note,
                created_at=h.created_at,
            )
            for h in obj.history.all()
        ]
        return cls(
            id=obj.pk,
            tracking_number=obj.tracking_number,
            postal_tracking=obj.postal_tracking,
            carrier_name=obj.carrier_name,
            shipped_at=obj.shipped_at,
            delivered_at=obj.delivered_at,
            customer_notes=obj.customer_notes,
            status=obj.status,
            status_display=_STATUS_DISPLAY_MAP.get(obj.status, obj.status),
            total_price=obj.total_price,
            shipping_cost=obj.shipping_cost,
            created_at=obj.created_at,
            shipping_address_snapshot=obj.shipping_address_snapshot,
            items=items,
            history=history,
        )