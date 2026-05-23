from decimal import Decimal
from typing import List, Optional

from ninja import Schema


# ── Province ────────────────────────────────────────────────────────────────

class ProvinceOut(Schema):
    id: int
    name: str
    code: str
    is_active: bool


class CityOut(Schema):
    id: int
    name: str
    code: str
    province_id: int
    is_active: bool


# ── ShippingZone ────────────────────────────────────────────────────────────

class ShippingZoneOut(Schema):
    id: int
    name: str
    provinces: List[str]


# ── ShippingMethod ──────────────────────────────────────────────────────────

class ShippingMethodOut(Schema):
    id: int
    name: str
    base_cost: Decimal
    cost_per_kg: Decimal
    free_above: Optional[Decimal] = None
    min_days: int
    max_days: int


class ShippingMethodDetailOut(Schema):
    id: int
    name: str
    slug: str
    carrier_name: str
    tracking_url_template: str
    base_cost: Decimal
    cost_per_kg: Decimal
    free_above: Optional[Decimal] = None
    min_days: int
    max_days: int
    is_active: bool


# ── ShippingOption (legacy — for POST /options) ────────────────────────────

class ShippingItemIn(Schema):
    product_id: int
    quantity: int


class ShippingOptionIn(Schema):
    province: str
    items: List[ShippingItemIn]


class ShippingOptionOut(Schema):
    id: int
    name: str
    cost: Decimal
    min_days: int
    max_days: int


# ── NEW: Calculate Shipping V2 ─────────────────────────────────────────────

class CalculateShippingIn(Schema):
    province_id: int
    city_id: Optional[int] = None
    total_weight: float = 0.0
    order_total: Decimal = Decimal("0")


class ShippingOptionV2Out(Schema):
    id: int
    name: str
    slug: str
    carrier_name: str
    tracking_url_template: str
    cost: Decimal
    min_days: int
    max_days: int


class CalculateShippingOut(Schema):
    province_id: int
    city_id: Optional[int] = None
    total_weight: float
    order_total: Decimal
    options: List[ShippingOptionV2Out]


# ── ShippingRate ────────────────────────────────────────────────────────────

class ShippingRateOut(Schema):
    id: int
    shipping_method_id: int
    shipping_method_name: str
    province_id: int
    province_name: str
    city_id: Optional[int] = None
    city_name: Optional[str] = None
    weight_min: Decimal
    weight_max: Decimal
    cost: Decimal
    is_active: bool


class ShippingRateCreateIn(Schema):
    shipping_method_id: int
    province_id: int
    city_id: Optional[int] = None
    weight_min: Decimal = Decimal("0")
    weight_max: Decimal = Decimal("1")
    cost: Decimal


class ShippingRateUpdateIn(Schema):
    weight_min: Optional[Decimal] = None
    weight_max: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    is_active: Optional[bool] = None
    city_id: Optional[int] = None
