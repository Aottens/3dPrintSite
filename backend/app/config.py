from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Literal


MaterialKey = Literal["PLA", "PETG", "ASA"]


@dataclass
class PricingParameters:
    density: Dict[MaterialKey, float] = field(
        default_factory=lambda: {"PLA": 1.24, "PETG": 1.27, "ASA": 1.07}
    )
    material_cost_per_g: Dict[MaterialKey, float] = field(
        default_factory=lambda: {"PLA": 0.045, "PETG": 0.055, "ASA": 0.06}
    )
    machine_rate_eur_per_hour: float = 15.0
    base_fee_eur: float = 4.0
    post_rate_eur_per_minute: float = 0.80
    risk_multiplier: float = 1.10
    minimum_item_price_eur: float = 6.0
    minimum_order_price_eur: float = 15.0
    setup_time_hours: float = 0.25


@dataclass
class PricingConfig:
    version: str
    effective_from: datetime
    parameters: PricingParameters
    created_by: str = "system"


DEFAULT_CONFIG = PricingConfig(
    version="1.0.0",
    effective_from=datetime(2024, 1, 1, 0, 0, 0),
    parameters=PricingParameters(),
)
