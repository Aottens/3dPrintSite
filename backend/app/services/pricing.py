"""
Pricing engine with versioned rule sets and deterministic calculations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import ceil
from typing import Any

from app.db.models import Material, PrintProfile, PricingRuleSet, Technology


@dataclass
class PriceBreakdown:
    """Detailed breakdown of price calculation."""

    material_cost: float
    machine_cost: float
    handling_fee: float
    support_cost: float
    quality_multiplier_applied: float
    risk_multiplier_applied: float
    subtotal: float
    minimum_applied: bool
    unit_price: float
    total_price: float
    lead_time_days: int


def estimate_print_time_hours(
    volume_cm3: float,
    profile: PrintProfile,
    technology: Technology,
) -> float:
    """
    Estimate print time based on volume and profile settings.

    For FDM: Based on extrusion speed and layer height
    For Resin: Based on exposure time per layer
    """
    if technology == Technology.RESIN:
        # Resin printing - time based on Z height and exposure
        # Assume 10 seconds per layer average
        # Estimate layers from volume (rough approximation)
        estimated_height_mm = (volume_cm3 * 1000) ** (1 / 3)  # Cube approximation
        layers = estimated_height_mm / profile.layer_height_mm
        time_hours = (layers * 10) / 3600  # 10 seconds per layer
    else:
        # FDM printing - time based on material volume and speed
        # Base print speed in mm^3/minute
        base_speed = 600
        adjusted_speed = base_speed * profile.speed_multiplier

        # Account for layer height effect
        layer_factor = 0.2 / profile.layer_height_mm
        adjusted_speed = adjusted_speed / layer_factor

        volume_mm3 = volume_cm3 * 1000
        minutes = max(volume_mm3 / adjusted_speed, 15)  # Minimum 15 minutes
        time_hours = minutes / 60

    # Apply quality multiplier (higher quality = more time)
    time_hours = time_hours * profile.quality_multiplier

    return round(time_hours, 2)


def calculate_price(
    *,
    volume_cm3: float,
    material: Material,
    profile: PrintProfile,
    rule_set: PricingRuleSet,
    quantity: int = 1,
) -> PriceBreakdown:
    """
    Calculate price for a print job.

    Args:
        volume_cm3: Model volume in cubic centimeters
        material: Selected material
        profile: Selected print profile
        rule_set: Pricing rule set to use
        quantity: Number of copies

    Returns:
        PriceBreakdown with all cost components
    """
    params = rule_set.parameters
    technology = Technology(profile.technology.value if hasattr(profile.technology, 'value') else profile.technology)

    # Get technology-specific machine rate
    machine_rates = params.get("machine_rate_eur_per_hour", {"fdm": 15.0, "resin": 25.0})
    if isinstance(machine_rates, dict):
        machine_rate = machine_rates.get(technology.value, 15.0)
    else:
        machine_rate = float(machine_rates)

    # Calculate material cost
    weight_g = volume_cm3 * material.density_g_cm3
    material_cost_per_g = material.cost_per_kg / 1000
    material_cost = weight_g * material_cost_per_g + material.surcharge

    # Calculate machine cost
    print_time_hours = estimate_print_time_hours(volume_cm3, profile, technology)
    setup_time = params.get("setup_time_hours", 0.25)
    total_machine_hours = max(print_time_hours + setup_time, setup_time)
    machine_cost = total_machine_hours * machine_rate

    # Base handling fee
    handling_fee = params.get("base_fee_eur", 4.0)

    # Support cost
    support_cost = 0.0
    if profile.supports_enabled:
        support_multiplier = params.get("support_multiplier", 1.15)
        support_cost = (material_cost + machine_cost) * (support_multiplier - 1)

    # Complexity multiplier for larger models
    complexity_threshold = params.get("complexity_threshold_cm3", 100)
    complexity_multiplier = params.get("complexity_multiplier", 1.05)
    complexity_factor = 1.0
    if volume_cm3 > complexity_threshold:
        complexity_factor = complexity_multiplier

    # Quality multiplier (already applied to time, affects total)
    quality_factor = profile.quality_multiplier

    # Risk multiplier
    risk_multiplier = params.get("risk_multiplier", 1.10)

    # Calculate subtotal
    subtotal = (material_cost + machine_cost + handling_fee + support_cost)
    subtotal = subtotal * complexity_factor * risk_multiplier

    # Apply minimums
    min_item_price = params.get("minimum_item_price_eur", 6.0)
    minimum_applied = False

    if subtotal < min_item_price:
        subtotal = min_item_price
        minimum_applied = True

    unit_price = round(subtotal, 2)

    # Calculate total
    total_price = unit_price * quantity

    # Apply order minimum
    min_order_price = params.get("minimum_order_price_eur", 15.0)
    if total_price < min_order_price:
        total_price = min_order_price
        minimum_applied = True

    total_price = round(total_price, 2)

    # Calculate lead time
    base_lead_time = params.get("base_lead_time_days", 3)
    # Add time for larger jobs
    additional_days = ceil(print_time_hours * quantity / 8)  # 8 hours per day
    lead_time_days = max(base_lead_time + additional_days, base_lead_time)

    return PriceBreakdown(
        material_cost=round(material_cost, 2),
        machine_cost=round(machine_cost, 2),
        handling_fee=round(handling_fee, 2),
        support_cost=round(support_cost, 2),
        quality_multiplier_applied=quality_factor,
        risk_multiplier_applied=risk_multiplier,
        subtotal=round(subtotal, 2),
        minimum_applied=minimum_applied,
        unit_price=unit_price,
        total_price=total_price,
        lead_time_days=lead_time_days,
    )


def create_breakdown_snapshot(breakdown: PriceBreakdown) -> dict[str, Any]:
    """Create a JSON-serializable snapshot of the price breakdown."""
    return {
        "material_cost": breakdown.material_cost,
        "machine_cost": breakdown.machine_cost,
        "handling_fee": breakdown.handling_fee,
        "support_cost": breakdown.support_cost,
        "quality_multiplier": breakdown.quality_multiplier_applied,
        "risk_multiplier": breakdown.risk_multiplier_applied,
        "subtotal": breakdown.subtotal,
        "minimum_applied": breakdown.minimum_applied,
        "unit_price": breakdown.unit_price,
        "total_price": breakdown.total_price,
        "lead_time_days": breakdown.lead_time_days,
    }


def get_quote_expiration() -> datetime:
    """Get the expiration datetime for a new quote (7 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=7)
