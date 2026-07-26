from decimal import Decimal
from typing import NamedTuple
from datetime import datetime as datetime, date as dtdate
import enum

class ReportReason(enum.StrEnum):
    FALSE_ADVERTISING = "false advertising",
    INNAPROPRIATE_CONTENT = "innapropriate content",
    CUSTOM = "custom"

class AddressEntry(NamedTuple):
    id: int
    country: str
    administrative_division: str | None
    city: str
    line1: str
    line2: str | None
    postal_code: str
    customer_id: int

class PaymentMethodEntry(NamedTuple):
    id: int
    card_number: str
    card_expiration: datetime
    card_code: int
    billing_address_id: int
    customer_id: int

class ProductEntry(NamedTuple):
    id: int
    product_name: str
    stock: int
    seller_id: int
    price: Decimal
    created_at: datetime

class PurchaseEntry(NamedTuple):
    id: int
    created_at: datetime
    customer_id: int
    payment_method_id: int

class ProductSalesEntry(NamedTuple):
    id: int
    purchase_id: int
    product_id: int
    price_per_item: Decimal
    quantity: int

class DeliveryEntry(NamedTuple):
    id: int
    purchase_id: int
    address_id: int
    delivery_status: str | None
    shipped_on: dtdate | None
    estimated_delivery_time: datetime | None

class RatingEntry(NamedTuple):
    customer_id: int
    product_id: int
    rating: int
    created_at: datetime

class ReportEntry(NamedTuple):
    id: int
    customer_id: int
    reviewed_by: int | None
    reason: str
    created_at: datetime

class PurchaseHistoryEntry(NamedTuple):
    purchase: PurchaseEntry
    deliveries: dict[int, tuple[DeliveryEntry, str]]
    sales: dict[int, tuple[ProductSalesEntry, str]]