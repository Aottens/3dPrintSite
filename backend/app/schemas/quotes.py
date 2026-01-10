"""
Quote and pricing schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ModelFileResponse(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    metrics_status: str
    volume_cm3: float | None
    surface_area_cm2: float | None
    bounding_box_mm: dict[str, float] | None
    is_manifold: bool | None
    is_watertight: bool | None
    metrics_error: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class QuoteRequest(BaseModel):
    model_file_id: str
    material_id: int
    color_id: int
    profile_id: int
    quantity: int = Field(ge=1, default=1)


class PriceBreakdown(BaseModel):
    material_cost: float
    machine_cost: float
    handling_fee: float
    support_cost: float
    quality_multiplier: float
    risk_multiplier: float
    subtotal: float
    minimum_applied: bool
    unit_price: float
    total_price: float


class QuoteResponse(BaseModel):
    id: str
    model_file_id: str
    material_id: int
    material_name: str
    color_id: int
    color_name: str
    profile_id: int
    profile_name: str
    quantity: int
    unit_price: float
    total_price: float
    lead_time_days: int
    breakdown: PriceBreakdown
    pricing_version: str
    is_valid: bool
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class PricingRuleSetResponse(BaseModel):
    id: int
    version: str
    name: str
    effective_from: datetime
    effective_to: datetime | None
    parameters: dict[str, Any]
    is_active: bool
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class PricingRuleSetCreateRequest(BaseModel):
    version: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    effective_from: datetime
    parameters: dict[str, Any]


class PricingRuleSetUpdateRequest(BaseModel):
    name: str | None = Field(min_length=1, max_length=100, default=None)
    effective_to: datetime | None = None
    parameters: dict[str, Any] | None = None
    is_active: bool | None = None
