"""
Quote API endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.db.models import (
    Material,
    MaterialColor,
    MetricsStatus,
    ModelFile,
    PricingRuleSet,
    PrintProfile,
    Quote,
)
from app.schemas.quotes import (
    PriceBreakdown,
    QuoteRequest,
    QuoteResponse,
)
from app.services.pricing import (
    calculate_price,
    create_breakdown_snapshot,
    get_quote_expiration,
)

router = APIRouter(prefix="/api/quotes", tags=["Quotes"])


async def get_current_pricing_rule_set(db) -> PricingRuleSet:
    """Get the currently active pricing rule set."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(PricingRuleSet)
        .where(
            PricingRuleSet.is_active == True,
            PricingRuleSet.effective_from <= now,
        )
        .order_by(PricingRuleSet.effective_from.desc())
        .limit(1)
    )
    rule_set = result.scalar_one_or_none()

    if not rule_set:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No active pricing rule set configured",
        )

    return rule_set


@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    request: QuoteRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """
    Create a new quote for a model.

    The model must have completed metrics calculation.
    """
    # Get model file
    result = await db.execute(
        select(ModelFile).where(
            ModelFile.id == request.model_file_id,
            ModelFile.user_id == current_user.id,
        )
    )
    model_file = result.scalar_one_or_none()

    if not model_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model file not found",
        )

    if model_file.metrics_status == MetricsStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model metrics are still being calculated. Please wait.",
        )

    if model_file.metrics_status == MetricsStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model metrics calculation in progress. Please wait.",
        )

    if model_file.metrics_status == MetricsStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model metrics calculation failed: {model_file.metrics_error}",
        )

    if model_file.volume_cm3 is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model volume not available",
        )

    # Get material with category
    result = await db.execute(
        select(Material)
        .options(selectinload(Material.category))
        .where(Material.id == request.material_id, Material.is_active == True)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found or inactive",
        )

    # Get color
    result = await db.execute(
        select(MaterialColor).where(
            MaterialColor.id == request.color_id,
            MaterialColor.material_id == request.material_id,
            MaterialColor.is_active == True,
        )
    )
    color = result.scalar_one_or_none()

    if not color:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Color not found or not available for this material",
        )

    # Get profile
    result = await db.execute(
        select(PrintProfile).where(
            PrintProfile.id == request.profile_id,
            PrintProfile.is_active == True,
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Print profile not found or inactive",
        )

    # Verify profile matches material technology
    if profile.technology != material.category.technology:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile technology ({profile.technology.value}) does not match material technology ({material.category.technology.value})",
        )

    # Get pricing rule set
    rule_set = await get_current_pricing_rule_set(db)

    # Calculate price
    breakdown = calculate_price(
        volume_cm3=model_file.volume_cm3,
        material=material,
        profile=profile,
        rule_set=rule_set,
        quantity=request.quantity,
    )

    # Create quote
    quote = Quote(
        user_id=current_user.id,
        model_file_id=model_file.id,
        material_id=material.id,
        color_id=color.id,
        profile_id=profile.id,
        pricing_rule_set_id=rule_set.id,
        quantity=request.quantity,
        unit_price=breakdown.unit_price,
        total_price=breakdown.total_price,
        lead_time_days=breakdown.lead_time_days,
        breakdown_snapshot=create_breakdown_snapshot(breakdown),
        pricing_params_snapshot=rule_set.parameters,
        is_valid=True,
        expires_at=get_quote_expiration(),
    )
    db.add(quote)
    await db.flush()
    await db.refresh(quote)

    return {
        "id": quote.id,
        "model_file_id": quote.model_file_id,
        "material_id": material.id,
        "material_name": f"{material.category.name} - {material.name}",
        "color_id": color.id,
        "color_name": color.name,
        "profile_id": profile.id,
        "profile_name": profile.name,
        "quantity": quote.quantity,
        "unit_price": quote.unit_price,
        "total_price": quote.total_price,
        "lead_time_days": quote.lead_time_days,
        "breakdown": PriceBreakdown(
            material_cost=breakdown.material_cost,
            machine_cost=breakdown.machine_cost,
            handling_fee=breakdown.handling_fee,
            support_cost=breakdown.support_cost,
            quality_multiplier=breakdown.quality_multiplier_applied,
            risk_multiplier=breakdown.risk_multiplier_applied,
            subtotal=breakdown.subtotal,
            minimum_applied=breakdown.minimum_applied,
            unit_price=breakdown.unit_price,
            total_price=breakdown.total_price,
        ),
        "pricing_version": rule_set.version,
        "is_valid": quote.is_valid,
        "expires_at": quote.expires_at,
        "created_at": quote.created_at,
    }


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Get a quote by ID."""
    result = await db.execute(
        select(Quote)
        .options(
            selectinload(Quote.material).selectinload(Material.category),
            selectinload(Quote.color),
            selectinload(Quote.profile),
            selectinload(Quote.pricing_rule_set),
        )
        .where(
            Quote.id == quote_id,
            Quote.user_id == current_user.id,
        )
    )
    quote = result.scalar_one_or_none()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found",
        )

    # Check if quote has expired
    if quote.expires_at < datetime.now(timezone.utc):
        quote.is_valid = False

    breakdown = quote.breakdown_snapshot

    return {
        "id": quote.id,
        "model_file_id": quote.model_file_id,
        "material_id": quote.material_id,
        "material_name": f"{quote.material.category.name} - {quote.material.name}",
        "color_id": quote.color_id,
        "color_name": quote.color.name,
        "profile_id": quote.profile_id,
        "profile_name": quote.profile.name,
        "quantity": quote.quantity,
        "unit_price": quote.unit_price,
        "total_price": quote.total_price,
        "lead_time_days": quote.lead_time_days,
        "breakdown": PriceBreakdown(
            material_cost=breakdown["material_cost"],
            machine_cost=breakdown["machine_cost"],
            handling_fee=breakdown["handling_fee"],
            support_cost=breakdown["support_cost"],
            quality_multiplier=breakdown["quality_multiplier"],
            risk_multiplier=breakdown["risk_multiplier"],
            subtotal=breakdown["subtotal"],
            minimum_applied=breakdown["minimum_applied"],
            unit_price=breakdown["unit_price"],
            total_price=breakdown["total_price"],
        ),
        "pricing_version": quote.pricing_rule_set.version,
        "is_valid": quote.is_valid,
        "expires_at": quote.expires_at,
        "created_at": quote.created_at,
    }


@router.get("", response_model=list[QuoteResponse])
async def list_quotes(
    current_user: CurrentUser,
    db: DbSession,
    valid_only: bool = False,
) -> list[dict]:
    """List all quotes for the current user."""
    query = (
        select(Quote)
        .options(
            selectinload(Quote.material).selectinload(Material.category),
            selectinload(Quote.color),
            selectinload(Quote.profile),
            selectinload(Quote.pricing_rule_set),
        )
        .where(Quote.user_id == current_user.id)
        .order_by(Quote.created_at.desc())
    )

    if valid_only:
        query = query.where(
            Quote.is_valid == True,
            Quote.expires_at > datetime.now(timezone.utc),
        )

    result = await db.execute(query)
    quotes = result.scalars().all()

    return [
        {
            "id": q.id,
            "model_file_id": q.model_file_id,
            "material_id": q.material_id,
            "material_name": f"{q.material.category.name} - {q.material.name}",
            "color_id": q.color_id,
            "color_name": q.color.name,
            "profile_id": q.profile_id,
            "profile_name": q.profile.name,
            "quantity": q.quantity,
            "unit_price": q.unit_price,
            "total_price": q.total_price,
            "lead_time_days": q.lead_time_days,
            "breakdown": PriceBreakdown(
                material_cost=q.breakdown_snapshot["material_cost"],
                machine_cost=q.breakdown_snapshot["machine_cost"],
                handling_fee=q.breakdown_snapshot["handling_fee"],
                support_cost=q.breakdown_snapshot["support_cost"],
                quality_multiplier=q.breakdown_snapshot["quality_multiplier"],
                risk_multiplier=q.breakdown_snapshot["risk_multiplier"],
                subtotal=q.breakdown_snapshot["subtotal"],
                minimum_applied=q.breakdown_snapshot["minimum_applied"],
                unit_price=q.breakdown_snapshot["unit_price"],
                total_price=q.breakdown_snapshot["total_price"],
            ),
            "pricing_version": q.pricing_rule_set.version,
            "is_valid": q.is_valid and q.expires_at > datetime.now(timezone.utc),
            "expires_at": q.expires_at,
            "created_at": q.created_at,
        }
        for q in quotes
    ]
