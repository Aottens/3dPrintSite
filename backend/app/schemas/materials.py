"""
Material and profile schemas.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class MaterialColorResponse(BaseModel):
    id: int
    name: str
    hex_code: str
    is_active: bool

    class Config:
        from_attributes = True


class MaterialResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    technology: str
    name: str
    brand: str
    density_g_cm3: float
    cost_per_kg: float
    surcharge: float
    is_active: bool
    colors: list[MaterialColorResponse]

    class Config:
        from_attributes = True


class MaterialCategoryResponse(BaseModel):
    id: int
    name: str
    technology: str
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class MaterialCreateRequest(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=100)
    brand: str = Field(min_length=1, max_length=100)
    density_g_cm3: float = Field(gt=0)
    cost_per_kg: float = Field(ge=0)
    surcharge: float = Field(ge=0, default=0.0)
    description: str | None = None


class MaterialUpdateRequest(BaseModel):
    name: str | None = Field(min_length=1, max_length=100, default=None)
    brand: str | None = Field(min_length=1, max_length=100, default=None)
    density_g_cm3: float | None = Field(gt=0, default=None)
    cost_per_kg: float | None = Field(ge=0, default=None)
    surcharge: float | None = Field(ge=0, default=None)
    description: str | None = None
    is_active: bool | None = None


class MaterialColorCreateRequest(BaseModel):
    material_id: int
    name: str = Field(min_length=1, max_length=50)
    hex_code: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")


class PrintProfileResponse(BaseModel):
    id: int
    technology: str
    name: str
    layer_height_mm: float
    infill_percentage: int
    supports_enabled: bool
    quality_multiplier: float
    speed_multiplier: float
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True


class PrintProfileCreateRequest(BaseModel):
    technology: str = Field(pattern=r"^(fdm|resin)$")
    name: str = Field(min_length=1, max_length=100)
    layer_height_mm: float = Field(gt=0, le=1.0)
    infill_percentage: int = Field(ge=0, le=100)
    supports_enabled: bool = False
    quality_multiplier: float = Field(gt=0, default=1.0)
    speed_multiplier: float = Field(gt=0, default=1.0)
    description: str | None = None


class PrintProfileUpdateRequest(BaseModel):
    name: str | None = Field(min_length=1, max_length=100, default=None)
    layer_height_mm: float | None = Field(gt=0, le=1.0, default=None)
    infill_percentage: int | None = Field(ge=0, le=100, default=None)
    supports_enabled: bool | None = None
    quality_multiplier: float | None = Field(gt=0, default=None)
    speed_multiplier: float | None = Field(gt=0, default=None)
    description: str | None = None
    is_active: bool | None = None
