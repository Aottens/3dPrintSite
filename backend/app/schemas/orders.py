"""
Order schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ShippingAddress(BaseModel):
    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    company_name: str | None = None


class OrderItemResponse(BaseModel):
    id: int
    quote_id: str
    status: str
    printer_assigned: str | None
    model_filename: str
    material_name: str
    color_name: str
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: str
    order_number: str
    user_id: str
    status: str
    shipping_address: dict[str, str]
    tracking_code: str | None
    subtotal: float
    shipping_cost: float
    total_price: float
    has_price_override: bool
    override_price: float | None
    override_reason: str | None
    notes: str | None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: str
    order_number: str
    status: str
    total_price: float
    item_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class OrderCreateRequest(BaseModel):
    quote_ids: list[str] = Field(min_length=1)
    shipping_address: ShippingAddress


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(
        pattern=r"^(new|in_planning|in_print|post_processing|shipped|completed|cancelled)$"
    )
    tracking_code: str | None = None
    notes: str | None = None


class PriceOverrideRequest(BaseModel):
    override_price: float = Field(ge=0)
    reason: str = Field(min_length=1, max_length=500)


class OrderStatusHistoryResponse(BaseModel):
    id: int
    from_status: str | None
    to_status: str
    changed_by: str
    notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    performed_by: str
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True
