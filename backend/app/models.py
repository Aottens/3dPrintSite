from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .config import PricingConfig, PricingParameters, DEFAULT_CONFIG, MaterialKey


@dataclass
class User:
    id: int
    name: str
    email: str
    password_hash: str
    role: str
    vat_number: Optional[str]
    addresses: List[str]


@dataclass
class Material:
    id: int
    family: str
    brand: str
    color_name: str
    hex: str
    density: float
    cost_per_kg: float
    surcharge: float
    active: bool = True


@dataclass
class ModelFile:
    id: int
    user_id: int
    filename: str
    volume_mm3: float
    surface_mm2: float
    bounding_box: List[float]
    weight_g: float
    upload_url: str


@dataclass
class Quote:
    id: int
    user_id: int
    model_id: int
    material_id: int
    quantity: int
    price: float
    config_version: str
    breakdown: Dict[str, float]
    lead_time_days: float


@dataclass
class Order:
    id: int
    user_id: int
    status: str
    tracking_code: Optional[str]
    created_at: datetime
    total_price: float


@dataclass
class OrderItem:
    order_id: int
    quote_id: int
    printer_assigned: Optional[str]
    status: str


@dataclass
class PricingConfigRecord:
    id: int
    version: str
    effective_from: datetime
    parameters: PricingParameters
    created_by: str


@dataclass
class PrinterJob:
    order_item_id: int
    printer_name: str
    start_time: datetime
    end_time: Optional[datetime]

    @property
    def duration_hr(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return None


class InMemoryDB:
    def __init__(self) -> None:
        self.users: Dict[int, User] = {}
        self.materials: Dict[int, Material] = {}
        self.models: Dict[int, ModelFile] = {}
        self.quotes: Dict[int, Quote] = {}
        self.orders: Dict[int, Order] = {}
        self.order_items: Dict[int, OrderItem] = {}
        self.pricing_configs: Dict[int, PricingConfigRecord] = {}
        self.printer_jobs: Dict[int, PrinterJob] = {}
        self._id_counters: Dict[str, int] = {}

        default_config = PricingConfigRecord(
            id=1,
            version=DEFAULT_CONFIG.version,
            effective_from=DEFAULT_CONFIG.effective_from,
            parameters=DEFAULT_CONFIG.parameters,
            created_by=DEFAULT_CONFIG.created_by,
        )
        self.pricing_configs[1] = default_config

    def _next_id(self, key: str) -> int:
        self._id_counters.setdefault(key, 0)
        self._id_counters[key] += 1
        return self._id_counters[key]

    def add_material(
        self,
        family: str,
        brand: str,
        color_name: str,
        hex_code: str,
        density: float,
        cost_per_kg: float,
        surcharge: float,
    ) -> Material:
        material_id = self._next_id("material")
        material = Material(
            id=material_id,
            family=family,
            brand=brand,
            color_name=color_name,
            hex=hex_code,
            density=density,
            cost_per_kg=cost_per_kg,
            surcharge=surcharge,
        )
        self.materials[material_id] = material
        return material

    def current_pricing_config(self) -> PricingConfigRecord:
        return max(self.pricing_configs.values(), key=lambda c: c.effective_from)


DB = InMemoryDB()
