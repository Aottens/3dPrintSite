"""Initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('customer', 'admin')")
    op.execute("CREATE TYPE technology AS ENUM ('fdm', 'resin')")
    op.execute("CREATE TYPE orderstatus AS ENUM ('new', 'in_planning', 'in_print', 'post_processing', 'shipped', 'completed', 'cancelled')")
    op.execute("CREATE TYPE metricsstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("customer", "admin", name="userrole", create_type=False), nullable=False, server_default="customer"),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("vat_number", sa.String(50), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Addresses table
    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(100), server_default="Default"),
        sa.Column("street", sa.String(255), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false"),
    )

    # Material categories table
    op.create_table(
        "material_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("technology", postgresql.ENUM("fdm", "resin", name="technology", create_type=False), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    # Materials table
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("material_categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("brand", sa.String(100), nullable=False),
        sa.Column("density_g_cm3", sa.Float(), nullable=False),
        sa.Column("cost_per_kg", sa.Float(), nullable=False),
        sa.Column("surcharge", sa.Float(), server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_materials_category_active", "materials", ["category_id", "is_active"])

    # Material colors table
    op.create_table(
        "material_colors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("hex_code", sa.String(7), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    # Print profiles table
    op.create_table(
        "print_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("technology", postgresql.ENUM("fdm", "resin", name="technology", create_type=False), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("layer_height_mm", sa.Float(), nullable=False),
        sa.Column("infill_percentage", sa.Integer(), nullable=False),
        sa.Column("supports_enabled", sa.Boolean(), server_default="false"),
        sa.Column("quality_multiplier", sa.Float(), server_default="1.0"),
        sa.Column("speed_multiplier", sa.Float(), server_default="1.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_print_profiles_technology_active", "print_profiles", ["technology", "is_active"])

    # Pricing rule sets table
    op.create_table(
        "pricing_rule_sets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("version", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parameters", postgresql.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_pricing_rule_sets_effective", "pricing_rule_sets", ["effective_from", "is_active"])

    # Model files table
    op.create_table(
        "model_files",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("metrics_status", postgresql.ENUM("pending", "processing", "completed", "failed", name="metricsstatus", create_type=False), server_default="pending"),
        sa.Column("volume_cm3", sa.Float(), nullable=True),
        sa.Column("surface_area_cm2", sa.Float(), nullable=True),
        sa.Column("bounding_box_mm", postgresql.JSON(), nullable=True),
        sa.Column("is_manifold", sa.Boolean(), nullable=True),
        sa.Column("is_watertight", sa.Boolean(), nullable=True),
        sa.Column("metrics_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Quotes table
    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_file_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("model_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("color_id", sa.Integer(), sa.ForeignKey("material_colors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("profile_id", sa.Integer(), sa.ForeignKey("print_profiles.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("pricing_rule_set_id", sa.Integer(), sa.ForeignKey("pricing_rule_sets.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=False),
        sa.Column("breakdown_snapshot", postgresql.JSON(), nullable=False),
        sa.Column("pricing_params_snapshot", postgresql.JSON(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Orders table
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("order_number", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", postgresql.ENUM("new", "in_planning", "in_print", "post_processing", "shipped", "completed", "cancelled", name="orderstatus", create_type=False), nullable=False, server_default="new"),
        sa.Column("shipping_address", postgresql.JSON(), nullable=False),
        sa.Column("tracking_code", sa.String(100), nullable=True),
        sa.Column("subtotal", sa.Float(), nullable=False),
        sa.Column("shipping_cost", sa.Float(), server_default="0"),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("has_price_override", sa.Boolean(), server_default="false"),
        sa.Column("override_price", sa.Float(), nullable=True),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_orders_user_status", "orders", ["user_id", "status"])
    op.create_index("ix_orders_created", "orders", ["created_at"])

    # Order items table
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("quotes.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", postgresql.ENUM("new", "in_planning", "in_print", "post_processing", "shipped", "completed", "cancelled", name="orderstatus", create_type=False), nullable=False, server_default="new"),
        sa.Column("printer_assigned", sa.String(100), nullable=True),
    )

    # Order status history table
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", postgresql.ENUM("new", "in_planning", "in_print", "post_processing", "shipped", "completed", "cancelled", name="orderstatus", create_type=False), nullable=True),
        sa.Column("to_status", postgresql.ENUM("new", "in_planning", "in_print", "post_processing", "shipped", "completed", "cancelled", name="orderstatus", create_type=False), nullable=False),
        sa.Column("changed_by", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Audit logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("old_value", postgresql.JSON(), nullable=True),
        sa.Column("new_value", postgresql.JSON(), nullable=True),
        sa.Column("performed_by", sa.String(255), nullable=False),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("order_status_history")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("quotes")
    op.drop_table("model_files")
    op.drop_table("pricing_rule_sets")
    op.drop_table("print_profiles")
    op.drop_table("material_colors")
    op.drop_table("materials")
    op.drop_table("material_categories")
    op.drop_table("addresses")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS metricsstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS technology")
    op.execute("DROP TYPE IF EXISTS userrole")
