from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import DEFAULT_CONFIG, PricingConfig
from .models import DB, ModelFile, Order, OrderItem, Quote, PricingConfigRecord
from .pricing import calculate_pricing

app = FastAPI(title="3D Print Service API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_pricing_config() -> PricingConfig:
    record = DB.current_pricing_config()
    return PricingConfig(
        version=record.version,
        effective_from=record.effective_from,
        parameters=record.parameters,
        created_by=record.created_by,
    )


class UploadResponse(BaseModel):
    model_id: int
    filename: str
    volume_mm3: float
    surface_mm2: float
    weight_g: float


class QuoteRequest(BaseModel):
    model_id: int
    material_id: int
    quantity: int = Field(ge=1, default=1)
    post_processing_minutes: float = Field(ge=0, default=0)


class QuoteResponse(BaseModel):
    quote_id: int
    unit_price: float
    total: float
    lead_time_days: float
    breakdown: dict
    config_version: str


class MaterialCreateRequest(BaseModel):
    family: str
    brand: str
    color_name: str
    hex: str
    density: float
    cost_per_kg: float
    surcharge: float = 0.0


class MaterialResponse(BaseModel):
    id: int
    family: str
    brand: str
    color_name: str
    hex: str
    density: float
    cost_per_kg: float
    surcharge: float
    active: bool


class PricingConfigResponse(BaseModel):
    version: str
    effective_from: datetime
    parameters: dict
    created_by: str


@app.post("/api/upload", response_model=UploadResponse)
async def upload_model(file: UploadFile) -> UploadResponse:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    model_id = len(DB.models) + 1
    size_mm3 = 50000.0
    surface = 20000.0
    weight = size_mm3 / 1000 * 1.24

    DB.models[model_id] = ModelFile(
        id=model_id,
        user_id=1,
        filename=file.filename,
        volume_mm3=size_mm3,
        surface_mm2=surface,
        bounding_box=[100, 100, 100],
        weight_g=weight,
        upload_url=f"/uploads/{model_id}/{file.filename}",
    )

    return UploadResponse(
        model_id=model_id,
        filename=file.filename,
        volume_mm3=size_mm3,
        surface_mm2=surface,
        weight_g=weight,
    )


@app.get("/api/materials", response_model=List[MaterialResponse])
def list_materials() -> List[MaterialResponse]:
    if not DB.materials:
        for family, density, cost in [
            ("PLA", 1.24, 45.0),
            ("PETG", 1.27, 55.0),
            ("ASA", 1.07, 60.0),
        ]:
            DB.add_material(
                family=family,
                brand="Generic",
                color_name="Natural",
                hex="#FFFFFF",
                density=density,
                cost_per_kg=cost,
                surcharge=0.0,
            )
    return [MaterialResponse(**vars(m)) for m in DB.materials.values()]


@app.post("/api/admin/material", response_model=MaterialResponse)
def create_material(payload: MaterialCreateRequest) -> MaterialResponse:
    material = DB.add_material(
        family=payload.family,
        brand=payload.brand,
        color_name=payload.color_name,
        hex_code=payload.hex,
        density=payload.density,
        cost_per_kg=payload.cost_per_kg,
        surcharge=payload.surcharge,
    )
    return MaterialResponse(**vars(material))


@app.post("/api/quote", response_model=QuoteResponse)
def create_quote(
    payload: QuoteRequest,
    config: PricingConfig = Depends(get_pricing_config),
) -> QuoteResponse:
    model = DB.models.get(payload.model_id)
    material = DB.materials.get(payload.material_id)

    if not model or not material:
        raise HTTPException(status_code=404, detail="Model or material not found")

    breakdown = calculate_pricing(
        config=config,
        material=material.family,  # type: ignore[arg-type]
        volume_mm3=model.volume_mm3,
        surface_mm2=model.surface_mm2,
        quantity=payload.quantity,
        post_processing_minutes=payload.post_processing_minutes,
    )

    quote_id = len(DB.quotes) + 1
    quote = Quote(
        id=quote_id,
        user_id=model.user_id,
        model_id=model.id,
        material_id=material.id,
        quantity=payload.quantity,
        price=breakdown["total"],
        config_version=config.version,
        breakdown=breakdown,
        lead_time_days=breakdown["lead_time_days"],
    )
    DB.quotes[quote_id] = quote

    return QuoteResponse(
        quote_id=quote_id,
        unit_price=breakdown["unit_price"],
        total=breakdown["total"],
        lead_time_days=breakdown["lead_time_days"],
        breakdown={k: v for k, v in breakdown.items() if k not in {"unit_price", "lead_time_days"}},
        config_version=config.version,
    )


@app.get("/api/admin/pricing/config", response_model=PricingConfigResponse)
def get_pricing() -> PricingConfigResponse:
    config = get_pricing_config()
    return PricingConfigResponse(
        version=config.version,
        effective_from=config.effective_from,
        parameters={
            "density": config.parameters.density,
            "material_cost_per_g": config.parameters.material_cost_per_g,
            "machine_rate_eur_per_hour": config.parameters.machine_rate_eur_per_hour,
            "base_fee_eur": config.parameters.base_fee_eur,
            "post_rate_eur_per_minute": config.parameters.post_rate_eur_per_minute,
            "risk_multiplier": config.parameters.risk_multiplier,
            "minimum_item_price_eur": config.parameters.minimum_item_price_eur,
            "minimum_order_price_eur": config.parameters.minimum_order_price_eur,
            "setup_time_hours": config.parameters.setup_time_hours,
        },
        created_by=config.created_by,
    )


class PricingConfigUpdateRequest(BaseModel):
    version: str
    effective_from: datetime
    parameters: dict
    created_by: str = "admin"


@app.post("/api/admin/pricing/config", response_model=PricingConfigResponse)
def update_pricing(payload: PricingConfigUpdateRequest) -> PricingConfigResponse:
    record_id = len(DB.pricing_configs) + 1
    params = DEFAULT_CONFIG.parameters.__class__(**payload.parameters)
    DB.pricing_configs[record_id] = PricingConfigRecord(
        id=record_id,
        version=payload.version,
        effective_from=payload.effective_from,
        parameters=params,
        created_by=payload.created_by,
    )
    return get_pricing()


class OrderRequest(BaseModel):
    quote_id: int
    shipping_address: str


class OrderResponse(BaseModel):
    order_id: int
    status: str
    total_price: float


@app.post("/api/order", response_model=OrderResponse)
def create_order(payload: OrderRequest) -> OrderResponse:
    quote = DB.quotes.get(payload.quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    order_id = len(DB.orders) + 1
    order = Order(
        id=order_id,
        user_id=quote.user_id,
        status="processing",
        tracking_code=None,
        created_at=datetime.utcnow(),
        total_price=quote.price,
    )
    DB.orders[order_id] = order

    item_id = len(DB.order_items) + 1
    DB.order_items[item_id] = OrderItem(
        order_id=order_id,
        quote_id=quote.id,
        printer_assigned=None,
        status="pending",
    )

    return OrderResponse(order_id=order_id, status=order.status, total_price=order.total_price)


class OrderDetailResponse(OrderResponse):
    tracking_code: Optional[str]
    created_at: datetime
    items: List[dict]


@app.get("/api/order/{order_id}", response_model=OrderDetailResponse)
def get_order(order_id: int) -> OrderDetailResponse:
    order = DB.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    related_items = [item for item in DB.order_items.values() if item.order_id == order_id]
    related_quotes = [DB.quotes[item.quote_id] for item in related_items if item.quote_id in DB.quotes]
    items = [
        {
            "quote_id": q.id,
            "material_id": q.material_id,
            "quantity": q.quantity,
            "status": next((item.status for item in related_items if item.quote_id == q.id), "processing"),
            "lead_time_days": q.lead_time_days,
        }
        for q in related_quotes
    ]
    return OrderDetailResponse(
        order_id=order.id,
        status=order.status,
        total_price=order.total_price,
        tracking_code=order.tracking_code,
        created_at=order.created_at,
        items=items,
    )


class OrderStatusUpdateRequest(BaseModel):
    status: str
    tracking_code: Optional[str] = None


@app.patch("/api/order/{order_id}/status", response_model=OrderDetailResponse)
def update_order_status(order_id: int, payload: OrderStatusUpdateRequest) -> OrderDetailResponse:
    order = DB.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.status
    order.tracking_code = payload.tracking_code or order.tracking_code

    for item in DB.order_items.values():
        if item.order_id == order_id:
            item.status = payload.status

    return get_order(order_id)
