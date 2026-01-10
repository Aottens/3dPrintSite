"""
Admin API endpoints.
"""

import csv
import io
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentAdminUser, DbSession
from app.db.models import (
    AuditLog,
    Material,
    MaterialCategory,
    MaterialColor,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    PricingRuleSet,
    PrintProfile,
    Quote,
    Technology,
    User,
)
from app.schemas.materials import (
    MaterialColorCreateRequest,
    MaterialCreateRequest,
    MaterialResponse,
    MaterialUpdateRequest,
    PrintProfileCreateRequest,
    PrintProfileResponse,
    PrintProfileUpdateRequest,
)
from app.schemas.orders import (
    AuditLogResponse,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
    PriceOverrideRequest,
)
from app.schemas.quotes import (
    PricingRuleSetCreateRequest,
    PricingRuleSetResponse,
    PricingRuleSetUpdateRequest,
)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============== Materials Management ==============


@router.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    request: MaterialCreateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict:
    """Create a new material."""
    # Verify category exists
    result = await db.execute(
        select(MaterialCategory).where(MaterialCategory.id == request.category_id)
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material category not found",
        )

    material = Material(
        category_id=request.category_id,
        name=request.name,
        brand=request.brand,
        density_g_cm3=request.density_g_cm3,
        cost_per_kg=request.cost_per_kg,
        surcharge=request.surcharge,
        description=request.description,
        is_active=True,
    )
    db.add(material)
    await db.flush()
    await db.refresh(material)

    return {
        "id": material.id,
        "category_id": material.category_id,
        "category_name": category.name,
        "technology": category.technology.value,
        "name": material.name,
        "brand": material.brand,
        "density_g_cm3": material.density_g_cm3,
        "cost_per_kg": material.cost_per_kg,
        "surcharge": material.surcharge,
        "is_active": material.is_active,
        "colors": [],
    }


@router.put("/materials/{material_id}", response_model=MaterialResponse)
async def update_material(
    material_id: int,
    request: MaterialUpdateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict:
    """Update a material."""
    result = await db.execute(
        select(Material)
        .options(selectinload(Material.category), selectinload(Material.colors))
        .where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    # Update fields
    if request.name is not None:
        material.name = request.name
    if request.brand is not None:
        material.brand = request.brand
    if request.density_g_cm3 is not None:
        material.density_g_cm3 = request.density_g_cm3
    if request.cost_per_kg is not None:
        material.cost_per_kg = request.cost_per_kg
    if request.surcharge is not None:
        material.surcharge = request.surcharge
    if request.description is not None:
        material.description = request.description
    if request.is_active is not None:
        material.is_active = request.is_active

    await db.flush()
    await db.refresh(material)

    return {
        "id": material.id,
        "category_id": material.category_id,
        "category_name": material.category.name,
        "technology": material.category.technology.value,
        "name": material.name,
        "brand": material.brand,
        "density_g_cm3": material.density_g_cm3,
        "cost_per_kg": material.cost_per_kg,
        "surcharge": material.surcharge,
        "is_active": material.is_active,
        "colors": [
            {"id": c.id, "name": c.name, "hex_code": c.hex_code, "is_active": c.is_active}
            for c in material.colors
        ],
    }


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: int,
    admin: CurrentAdminUser,
    db: DbSession,
) -> None:
    """Delete a material (soft delete by setting is_active=False)."""
    result = await db.execute(
        select(Material).where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    material.is_active = False


@router.post("/materials/colors", status_code=status.HTTP_201_CREATED)
async def create_material_color(
    request: MaterialColorCreateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> MaterialColor:
    """Add a color to a material."""
    result = await db.execute(
        select(Material).where(Material.id == request.material_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    color = MaterialColor(
        material_id=request.material_id,
        name=request.name,
        hex_code=request.hex_code,
        is_active=True,
    )
    db.add(color)
    await db.flush()
    await db.refresh(color)

    return color


# ============== Print Profiles Management ==============


@router.post("/profiles", response_model=PrintProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    request: PrintProfileCreateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> PrintProfile:
    """Create a new print profile."""
    profile = PrintProfile(
        technology=Technology(request.technology),
        name=request.name,
        layer_height_mm=request.layer_height_mm,
        infill_percentage=request.infill_percentage,
        supports_enabled=request.supports_enabled,
        quality_multiplier=request.quality_multiplier,
        speed_multiplier=request.speed_multiplier,
        description=request.description,
        is_active=True,
    )
    db.add(profile)
    await db.flush()
    await db.refresh(profile)

    return profile


@router.put("/profiles/{profile_id}", response_model=PrintProfileResponse)
async def update_profile(
    profile_id: int,
    request: PrintProfileUpdateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> PrintProfile:
    """Update a print profile."""
    result = await db.execute(
        select(PrintProfile).where(PrintProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    if request.name is not None:
        profile.name = request.name
    if request.layer_height_mm is not None:
        profile.layer_height_mm = request.layer_height_mm
    if request.infill_percentage is not None:
        profile.infill_percentage = request.infill_percentage
    if request.supports_enabled is not None:
        profile.supports_enabled = request.supports_enabled
    if request.quality_multiplier is not None:
        profile.quality_multiplier = request.quality_multiplier
    if request.speed_multiplier is not None:
        profile.speed_multiplier = request.speed_multiplier
    if request.description is not None:
        profile.description = request.description
    if request.is_active is not None:
        profile.is_active = request.is_active

    await db.flush()
    await db.refresh(profile)

    return profile


# ============== Pricing Rule Sets Management ==============


@router.get("/pricing", response_model=list[PricingRuleSetResponse])
async def list_pricing_rule_sets(
    admin: CurrentAdminUser,
    db: DbSession,
) -> list[PricingRuleSet]:
    """List all pricing rule sets."""
    result = await db.execute(
        select(PricingRuleSet).order_by(PricingRuleSet.effective_from.desc())
    )
    return list(result.scalars().all())


@router.get("/pricing/current", response_model=PricingRuleSetResponse)
async def get_current_pricing(
    admin: CurrentAdminUser,
    db: DbSession,
) -> PricingRuleSet:
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active pricing rule set found",
        )

    return rule_set


@router.post("/pricing", response_model=PricingRuleSetResponse, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule_set(
    request: PricingRuleSetCreateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> PricingRuleSet:
    """Create a new pricing rule set."""
    # Check version uniqueness
    result = await db.execute(
        select(PricingRuleSet).where(PricingRuleSet.version == request.version)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version already exists",
        )

    rule_set = PricingRuleSet(
        version=request.version,
        name=request.name,
        effective_from=request.effective_from,
        parameters=request.parameters,
        is_active=True,
        created_by=admin.email,
    )
    db.add(rule_set)
    await db.flush()
    await db.refresh(rule_set)

    return rule_set


@router.put("/pricing/{rule_set_id}", response_model=PricingRuleSetResponse)
async def update_pricing_rule_set(
    rule_set_id: int,
    request: PricingRuleSetUpdateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
) -> PricingRuleSet:
    """Update a pricing rule set."""
    result = await db.execute(
        select(PricingRuleSet).where(PricingRuleSet.id == rule_set_id)
    )
    rule_set = result.scalar_one_or_none()

    if not rule_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing rule set not found",
        )

    if request.name is not None:
        rule_set.name = request.name
    if request.effective_to is not None:
        rule_set.effective_to = request.effective_to
    if request.parameters is not None:
        rule_set.parameters = request.parameters
    if request.is_active is not None:
        rule_set.is_active = request.is_active

    await db.flush()
    await db.refresh(rule_set)

    return rule_set


# ============== Orders Management ==============


@router.get("/orders", response_model=list[OrderResponse])
async def list_all_orders(
    admin: CurrentAdminUser,
    db: DbSession,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """List all orders (admin view)."""
    query = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.quote).options(
                selectinload(Quote.material).selectinload(Material.category),
                selectinload(Quote.color),
                selectinload(Quote.model_file),
            ),
            selectinload(Order.user),
        )
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
            query = query.where(Order.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status_filter}",
            )

    result = await db.execute(query)
    orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "order_number": o.order_number,
            "user_id": o.user_id,
            "status": o.status.value,
            "shipping_address": o.shipping_address,
            "tracking_code": o.tracking_code,
            "subtotal": o.subtotal,
            "shipping_cost": o.shipping_cost,
            "total_price": o.total_price,
            "has_price_override": o.has_price_override,
            "override_price": o.override_price,
            "override_reason": o.override_reason,
            "notes": o.notes,
            "items": [
                OrderItemResponse(
                    id=item.id,
                    quote_id=item.quote_id,
                    status=item.status.value,
                    printer_assigned=item.printer_assigned,
                    model_filename=item.quote.model_file.original_filename,
                    material_name=f"{item.quote.material.category.name} - {item.quote.material.name}",
                    color_name=item.quote.color.name,
                    quantity=item.quote.quantity,
                    unit_price=item.quote.unit_price,
                )
                for item in o.items
            ],
            "created_at": o.created_at,
            "updated_at": o.updated_at,
        }
        for o in orders
    ]


@router.patch("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    request: OrderStatusUpdateRequest,
    admin: CurrentAdminUser,
    db: DbSession,
    http_request: Request,
) -> dict:
    """Update order status."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.quote).options(
                selectinload(Quote.material).selectinload(Material.category),
                selectinload(Quote.color),
                selectinload(Quote.model_file),
            )
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    old_status = order.status
    new_status = OrderStatus(request.status)

    # Update order
    order.status = new_status
    if request.tracking_code:
        order.tracking_code = request.tracking_code
    if request.notes:
        order.notes = request.notes

    # Update item statuses
    for item in order.items:
        item.status = new_status

    # Create status history entry
    history = OrderStatusHistory(
        order_id=order.id,
        from_status=old_status,
        to_status=new_status,
        changed_by=admin.email,
        notes=request.notes,
    )
    db.add(history)

    # Create audit log
    audit = AuditLog(
        order_id=order.id,
        action="status_update",
        entity_type="order",
        entity_id=order.id,
        old_value={"status": old_status.value},
        new_value={"status": new_status.value, "tracking_code": request.tracking_code},
        performed_by=admin.email,
        ip_address=http_request.client.host if http_request.client else None,
    )
    db.add(audit)

    await db.flush()
    await db.refresh(order)

    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "status": order.status.value,
        "shipping_address": order.shipping_address,
        "tracking_code": order.tracking_code,
        "subtotal": order.subtotal,
        "shipping_cost": order.shipping_cost,
        "total_price": order.total_price,
        "has_price_override": order.has_price_override,
        "override_price": order.override_price,
        "override_reason": order.override_reason,
        "notes": order.notes,
        "items": [
            OrderItemResponse(
                id=item.id,
                quote_id=item.quote_id,
                status=item.status.value,
                printer_assigned=item.printer_assigned,
                model_filename=item.quote.model_file.original_filename,
                material_name=f"{item.quote.material.category.name} - {item.quote.material.name}",
                color_name=item.quote.color.name,
                quantity=item.quote.quantity,
                unit_price=item.quote.unit_price,
            )
            for item in order.items
        ],
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


@router.post("/orders/{order_id}/override-price", response_model=OrderResponse)
async def override_order_price(
    order_id: str,
    request: PriceOverrideRequest,
    admin: CurrentAdminUser,
    db: DbSession,
    http_request: Request,
) -> dict:
    """Override order price (with audit log)."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.quote).options(
                selectinload(Quote.material).selectinload(Material.category),
                selectinload(Quote.color),
                selectinload(Quote.model_file),
            )
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    old_price = order.total_price

    # Apply override
    order.has_price_override = True
    order.override_price = request.override_price
    order.override_reason = request.reason
    order.total_price = request.override_price

    # Create audit log
    audit = AuditLog(
        order_id=order.id,
        action="price_override",
        entity_type="order",
        entity_id=order.id,
        old_value={"total_price": old_price, "has_override": False},
        new_value={
            "total_price": request.override_price,
            "has_override": True,
            "reason": request.reason,
        },
        performed_by=admin.email,
        ip_address=http_request.client.host if http_request.client else None,
    )
    db.add(audit)

    await db.flush()
    await db.refresh(order)

    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "status": order.status.value,
        "shipping_address": order.shipping_address,
        "tracking_code": order.tracking_code,
        "subtotal": order.subtotal,
        "shipping_cost": order.shipping_cost,
        "total_price": order.total_price,
        "has_price_override": order.has_price_override,
        "override_price": order.override_price,
        "override_reason": order.override_reason,
        "notes": order.notes,
        "items": [
            OrderItemResponse(
                id=item.id,
                quote_id=item.quote_id,
                status=item.status.value,
                printer_assigned=item.printer_assigned,
                model_filename=item.quote.model_file.original_filename,
                material_name=f"{item.quote.material.category.name} - {item.quote.material.name}",
                color_name=item.quote.color.name,
                quantity=item.quote.quantity,
                unit_price=item.quote.unit_price,
            )
            for item in order.items
        ],
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


@router.get("/orders/{order_id}/audit", response_model=list[AuditLogResponse])
async def get_order_audit_log(
    order_id: str,
    admin: CurrentAdminUser,
    db: DbSession,
) -> list[AuditLog]:
    """Get audit log for an order."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.order_id == order_id)
        .order_by(AuditLog.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/orders/export/csv")
async def export_orders_csv(
    admin: CurrentAdminUser,
    db: DbSession,
    status_filter: str | None = Query(None, alias="status"),
) -> StreamingResponse:
    """Export orders to CSV."""
    query = (
        select(Order)
        .options(selectinload(Order.user))
        .order_by(Order.created_at.desc())
    )

    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
            query = query.where(Order.status == status_enum)
        except ValueError:
            pass

    result = await db.execute(query)
    orders = result.scalars().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Order Number",
        "Status",
        "Customer Email",
        "Subtotal",
        "Shipping",
        "Total",
        "Has Override",
        "Override Price",
        "Created At",
    ])

    for order in orders:
        writer.writerow([
            order.order_number,
            order.status.value,
            order.user.email if order.user else "",
            order.subtotal,
            order.shipping_cost,
            order.total_price,
            order.has_price_override,
            order.override_price or "",
            order.created_at.isoformat(),
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="orders_{datetime.now().strftime("%Y%m%d")}.csv"'
        },
    )


# ============== Analytics ==============


@router.get("/analytics/summary")
async def get_analytics_summary(
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict[str, Any]:
    """Get analytics summary for dashboard."""
    now = datetime.now(timezone.utc)

    # Orders in last 7 days
    from datetime import timedelta

    week_ago = now - timedelta(days=7)

    result = await db.execute(
        select(func.count(Order.id)).where(Order.created_at >= week_ago)
    )
    orders_7d = result.scalar() or 0

    # Revenue in last 7 days
    result = await db.execute(
        select(func.sum(Order.total_price)).where(Order.created_at >= week_ago)
    )
    revenue_7d = result.scalar() or 0

    # Top material (by order count)
    result = await db.execute(
        select(
            Material.name,
            func.count(OrderItem.id).label("count"),
        )
        .join(Quote, OrderItem.quote_id == Quote.id)
        .join(Material, Quote.material_id == Material.id)
        .group_by(Material.name)
        .order_by(func.count(OrderItem.id).desc())
        .limit(1)
    )
    top_material_row = result.first()
    top_material = top_material_row[0] if top_material_row else "N/A"
    top_material_count = top_material_row[1] if top_material_row else 0

    # Average lead time
    result = await db.execute(
        select(func.avg(Quote.lead_time_days))
    )
    avg_lead_time = result.scalar() or 0

    return {
        "orders_7d": orders_7d,
        "revenue_7d": float(revenue_7d),
        "top_material": top_material,
        "top_material_orders": top_material_count,
        "avg_lead_time_days": round(float(avg_lead_time), 1),
    }


# ============== Users Management ==============


@router.get("/users")
async def list_users(
    admin: CurrentAdminUser,
    db: DbSession,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """List all users."""
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    users = result.scalars().all()

    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role.value,
            "company_name": u.company_name,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    admin: CurrentAdminUser,
    db: DbSession,
) -> dict:
    """Enable or disable a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent disabling self
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot disable your own account",
        )

    user.is_active = not user.is_active
    await db.flush()

    return {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
    }
