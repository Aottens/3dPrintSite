"""
Order API endpoints.
"""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.db.models import (
    Material,
    ModelFile,
    Order,
    OrderItem,
    OrderStatus,
    OrderStatusHistory,
    Quote,
)
from app.schemas.orders import (
    OrderCreateRequest,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
)

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def generate_order_number() -> str:
    """Generate a unique order number."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique = uuid4().hex[:6].upper()
    return f"NP-{timestamp}-{unique}"


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: OrderCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """
    Create an order from one or more quotes.

    All quotes must be valid and not expired.
    """
    if not request.quote_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one quote is required",
        )

    # Get all quotes
    result = await db.execute(
        select(Quote)
        .options(
            selectinload(Quote.material).selectinload(Material.category),
            selectinload(Quote.color),
            selectinload(Quote.model_file),
        )
        .where(
            Quote.id.in_(request.quote_ids),
            Quote.user_id == current_user.id,
        )
    )
    quotes = list(result.scalars().all())

    if len(quotes) != len(request.quote_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more quotes not found",
        )

    # Validate all quotes
    now = datetime.now(timezone.utc)
    for quote in quotes:
        if not quote.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quote {quote.id} is no longer valid",
            )
        if quote.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quote {quote.id} has expired",
            )

    # Calculate totals
    subtotal = sum(q.total_price for q in quotes)
    shipping_cost = 0.0  # Could be calculated based on weight/destination
    total_price = subtotal + shipping_cost

    # Create order
    order = Order(
        order_number=generate_order_number(),
        user_id=current_user.id,
        status=OrderStatus.NEW,
        shipping_address={
            "street": request.shipping_address.street,
            "city": request.shipping_address.city,
            "postal_code": request.shipping_address.postal_code,
            "country": request.shipping_address.country,
            "company_name": request.shipping_address.company_name,
        },
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total_price=total_price,
    )
    db.add(order)
    await db.flush()

    # Create order items
    items = []
    for quote in quotes:
        item = OrderItem(
            order_id=order.id,
            quote_id=quote.id,
            status=OrderStatus.NEW,
        )
        db.add(item)
        items.append(item)

        # Invalidate quote (can only be used once)
        quote.is_valid = False

    # Create initial status history entry
    history = OrderStatusHistory(
        order_id=order.id,
        from_status=None,
        to_status=OrderStatus.NEW,
        changed_by=current_user.email,
        notes="Order created",
    )
    db.add(history)

    await db.flush()
    await db.refresh(order)

    # Build response
    order_items = []
    for item, quote in zip(items, quotes):
        order_items.append(
            OrderItemResponse(
                id=item.id if hasattr(item, 'id') else 0,
                quote_id=quote.id,
                status=item.status.value,
                printer_assigned=item.printer_assigned,
                model_filename=quote.model_file.original_filename,
                material_name=f"{quote.material.category.name} - {quote.material.name}",
                color_name=quote.color.name,
                quantity=quote.quantity,
                unit_price=quote.unit_price,
            )
        )

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
        "items": order_items,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


@router.get("", response_model=list[OrderListResponse])
async def list_orders(
    current_user: CurrentUser,
    db: DbSession,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
) -> list[dict]:
    """List orders for the current user."""
    query = (
        select(
            Order,
            func.count(OrderItem.id).label("item_count"),
        )
        .outerjoin(OrderItem)
        .where(Order.user_id == current_user.id)
        .group_by(Order.id)
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
    rows = result.all()

    return [
        {
            "id": row.Order.id,
            "order_number": row.Order.order_number,
            "status": row.Order.status.value,
            "total_price": row.Order.total_price,
            "item_count": row.item_count,
            "created_at": row.Order.created_at,
        }
        for row in rows
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    """Get order details."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.quote).options(
                selectinload(Quote.material).selectinload(Material.category),
                selectinload(Quote.color),
                selectinload(Quote.model_file),
            )
        )
        .where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order_items = [
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
    ]

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
        "items": order_items,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


@router.get("/{order_id}/history", response_model=list[OrderStatusHistoryResponse])
async def get_order_history(
    order_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> list[OrderStatusHistory]:
    """Get order status history."""
    # Verify order belongs to user
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    # Get history
    result = await db.execute(
        select(OrderStatusHistory)
        .where(OrderStatusHistory.order_id == order_id)
        .order_by(OrderStatusHistory.created_at.desc())
    )

    return list(result.scalars().all())
