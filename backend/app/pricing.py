from __future__ import annotations

from math import ceil
from typing import Dict

from .config import MaterialKey, PricingConfig


def estimate_print_time_hours(volume_mm3: float, layer_height_mm: float = 0.2) -> float:
    base_speed_mm3_per_minute = 600  # placeholder average print speed
    volume_cm3 = volume_mm3 / 1000.0
    minutes = max(volume_cm3 * 1000 / base_speed_mm3_per_minute, 15)
    return minutes / 60


def calculate_pricing(
    *,
    config: PricingConfig,
    material: MaterialKey,
    volume_mm3: float,
    surface_mm2: float,
    quantity: int,
    post_processing_minutes: float = 0.0,
) -> Dict[str, float]:
    params = config.parameters
    density = params.density[material]
    weight_g = volume_mm3 / 1000.0 * density
    material_cost = weight_g * params.material_cost_per_g[material]

    machine_time_hours = max(estimate_print_time_hours(volume_mm3), params.setup_time_hours)
    machine_cost = machine_time_hours * params.machine_rate_eur_per_hour

    post_cost = post_processing_minutes * params.post_rate_eur_per_minute

    subtotal = (material_cost + machine_cost + params.base_fee_eur + post_cost) * params.risk_multiplier
    item_total = max(subtotal, params.minimum_item_price_eur)
    order_total = max(item_total * quantity, params.minimum_order_price_eur)

    return {
        "material": round(material_cost, 2),
        "machine": round(machine_cost, 2),
        "base": round(params.base_fee_eur, 2),
        "post": round(post_cost, 2),
        "total": round(order_total, 2),
        "unit_price": round(item_total, 2),
        "lead_time_days": round(max(ceil(machine_time_hours * quantity / 8), 1), 1),
    }
