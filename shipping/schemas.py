from decimal import Decimal
from typing import List, Optional

from ninja import Schema


# ── ShippingZone ──────────────────────────────────────────────────────────────

class ShippingZoneOut(Schema):
    id: int
    name: str
    provinces: List[str]


# ── ShippingMethod ────────────────────────────────────────────────────────────

class ShippingMethodOut(Schema):
    id: int
    name: str
    base_cost: Decimal
    cost_per_kg: Decimal
    free_above: Optional[Decimal] = None
    min_days: int
    max_days: int


# ── ShippingOption (برای POST /options) ───────────────────────────────────────

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
