from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def generate_uuid() -> str:
    return str(uuid4())


class UserRole(str, PyEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class Technology(str, PyEnum):
    FDM = "fdm"
    RESIN = "resin"


class OrderStatus(str, PyEnum):
    NEW = "new"
    IN_PLANNING = "in_planning"
    IN_PRINT = "in_print"
    POST_PROCESSING = "post_processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MetricsStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.CUSTOMER, nullable=False
    )
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vat_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    model_files: Mapped[list["ModelFile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), default="Default")
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="addresses")


class MaterialCategory(Base):
    __tablename__ = "material_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    technology: Mapped[Technology] = mapped_column(Enum(Technology), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    materials: Mapped[list["Material"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("material_categories.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    density_g_cm3: Mapped[float] = mapped_column(Float, nullable=False)
    cost_per_kg: Mapped[float] = mapped_column(Float, nullable=False)
    surcharge: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    category: Mapped["MaterialCategory"] = relationship(back_populates="materials")
    colors: Mapped[list["MaterialColor"]] = relationship(back_populates="material", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_materials_category_active", "category_id", "is_active"),
    )


class MaterialColor(Base):
    __tablename__ = "material_colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    hex_code: Mapped[str] = mapped_column(String(7), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    material: Mapped["Material"] = relationship(back_populates="colors")


class PrintProfile(Base):
    __tablename__ = "print_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    technology: Mapped[Technology] = mapped_column(Enum(Technology), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    layer_height_mm: Mapped[float] = mapped_column(Float, nullable=False)
    infill_percentage: Mapped[int] = mapped_column(Integer, nullable=False)
    supports_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    speed_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_print_profiles_technology_active", "technology", "is_active"),
    )


class PricingRuleSet(Base):
    __tablename__ = "pricing_rule_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_pricing_rule_sets_effective", "effective_from", "is_active"),
    )


class ModelFile(Base):
    __tablename__ = "model_files"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Metrics (populated by background job)
    metrics_status: Mapped[MetricsStatus] = mapped_column(
        Enum(MetricsStatus), default=MetricsStatus.PENDING
    )
    volume_cm3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    surface_area_cm2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bounding_box_mm: Mapped[Optional[dict[str, float]]] = mapped_column(JSON, nullable=True)
    is_manifold: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_watertight: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    metrics_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="model_files")
    quotes: Mapped[list["Quote"]] = relationship(back_populates="model_file", cascade="all, delete-orphan")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    model_file_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("model_files.id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False
    )
    color_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("material_colors.id", ondelete="RESTRICT"), nullable=False
    )
    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("print_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    pricing_rule_set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pricing_rule_sets.id", ondelete="RESTRICT"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Full breakdown snapshot for audit
    breakdown_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    pricing_params_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="quotes")
    model_file: Mapped["ModelFile"] = relationship(back_populates="quotes")
    material: Mapped["Material"] = relationship()
    color: Mapped["MaterialColor"] = relationship()
    profile: Mapped["PrintProfile"] = relationship()
    pricing_rule_set: Mapped["PricingRuleSet"] = relationship()
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="quote")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=generate_uuid
    )
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW, nullable=False
    )

    # Shipping
    shipping_address: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False)
    tracking_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Pricing
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Manual override
    has_price_override: Mapped[bool] = mapped_column(Boolean, default=False)
    override_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        Index("ix_orders_created", "created_at"),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    quote_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.NEW, nullable=False
    )
    printer_assigned: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    order: Mapped["Order"] = relationship(back_populates="items")
    quote: Mapped["Quote"] = relationship(back_populates="order_items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[Optional[OrderStatus]] = mapped_column(Enum(OrderStatus), nullable=True)
    to_status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    order: Mapped["Order"] = relationship(back_populates="status_history")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("orders.id", ondelete="CASCADE"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    old_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    performed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    order: Mapped[Optional["Order"]] = relationship(back_populates="audit_logs")

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_created", "created_at"),
    )
