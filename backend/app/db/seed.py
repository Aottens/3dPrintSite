"""
Seed data for NovaPrint database.

This module provides initial data for development and testing:
- 2 technologies (FDM, Resin)
- 6+ materials across technologies
- Multiple colors per material
- Print profiles per technology
- 1 admin account
- 1 demo customer account
- Default pricing rule set
"""

import asyncio
from datetime import datetime, timezone

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_maker
from app.db.models import (
    Material,
    MaterialCategory,
    MaterialColor,
    PricingRuleSet,
    PrintProfile,
    Technology,
    User,
    UserRole,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_users(session: AsyncSession) -> dict[str, User]:
    """Create admin and demo user accounts."""
    users = {}

    # Check if admin exists
    result = await session.execute(
        select(User).where(User.email == "admin@novaprint.local")
    )
    admin = result.scalar_one_or_none()

    if not admin:
        admin = User(
            email="admin@novaprint.local",
            name="Admin User",
            password_hash=pwd_context.hash("admin123"),
            role=UserRole.ADMIN,
            company_name="NovaPrint",
            is_active=True,
        )
        session.add(admin)
        users["admin"] = admin

    # Check if demo user exists
    result = await session.execute(
        select(User).where(User.email == "demo@example.com")
    )
    demo = result.scalar_one_or_none()

    if not demo:
        demo = User(
            email="demo@example.com",
            name="Demo Customer",
            password_hash=pwd_context.hash("demo123"),
            role=UserRole.CUSTOMER,
            company_name="Demo Company",
            is_active=True,
        )
        session.add(demo)
        users["demo"] = demo

    await session.flush()
    return users


async def seed_material_categories(session: AsyncSession) -> dict[str, MaterialCategory]:
    """Create material categories for each technology."""
    categories = {}

    fdm_categories = [
        ("PLA", Technology.FDM, "Polylactic Acid - Easy to print, biodegradable"),
        ("PETG", Technology.FDM, "Polyethylene Terephthalate Glycol - Strong and flexible"),
        ("ASA", Technology.FDM, "Acrylonitrile Styrene Acrylate - UV resistant"),
        ("ABS", Technology.FDM, "Acrylonitrile Butadiene Styrene - Strong and heat resistant"),
    ]

    resin_categories = [
        ("Standard Resin", Technology.RESIN, "General purpose UV resin"),
        ("Tough Resin", Technology.RESIN, "High impact resistance resin"),
    ]

    for name, tech, description in fdm_categories + resin_categories:
        result = await session.execute(
            select(MaterialCategory).where(MaterialCategory.name == name)
        )
        category = result.scalar_one_or_none()

        if not category:
            category = MaterialCategory(
                name=name,
                technology=tech,
                description=description,
                is_active=True,
            )
            session.add(category)

        categories[name] = category

    await session.flush()
    return categories


async def seed_materials(
    session: AsyncSession, categories: dict[str, MaterialCategory]
) -> dict[str, Material]:
    """Create materials with colors."""
    materials = {}

    material_data = [
        # FDM Materials
        {
            "category": "PLA",
            "name": "PLA Standard",
            "brand": "Prusament",
            "density": 1.24,
            "cost_per_kg": 25.0,
            "colors": [
                ("Galaxy Black", "#1a1a2e"),
                ("Jet Black", "#000000"),
                ("Pearl White", "#f5f5f5"),
                ("Signal Red", "#ff0000"),
                ("Lime Green", "#32cd32"),
                ("Ocean Blue", "#0066cc"),
            ],
        },
        {
            "category": "PLA",
            "name": "PLA Silk",
            "brand": "Prusament",
            "density": 1.24,
            "cost_per_kg": 32.0,
            "surcharge": 2.0,
            "colors": [
                ("Silk Gold", "#ffd700"),
                ("Silk Silver", "#c0c0c0"),
                ("Silk Copper", "#b87333"),
            ],
        },
        {
            "category": "PETG",
            "name": "PETG Standard",
            "brand": "Prusament",
            "density": 1.27,
            "cost_per_kg": 28.0,
            "colors": [
                ("Clear", "#e0e0e0"),
                ("Jet Black", "#000000"),
                ("Ultramarine Blue", "#4169e1"),
                ("Prusa Orange", "#fa6900"),
            ],
        },
        {
            "category": "ASA",
            "name": "ASA Standard",
            "brand": "Prusament",
            "density": 1.07,
            "cost_per_kg": 35.0,
            "colors": [
                ("Natural", "#f5f5dc"),
                ("Jet Black", "#000000"),
                ("Galaxy Black", "#1a1a2e"),
            ],
        },
        {
            "category": "ABS",
            "name": "ABS Standard",
            "brand": "Prusament",
            "density": 1.04,
            "cost_per_kg": 26.0,
            "colors": [
                ("Black", "#000000"),
                ("White", "#ffffff"),
                ("Red", "#ff0000"),
            ],
        },
        # Resin Materials
        {
            "category": "Standard Resin",
            "name": "Standard Grey",
            "brand": "Elegoo",
            "density": 1.10,
            "cost_per_kg": 35.0,
            "colors": [
                ("Grey", "#808080"),
                ("Black", "#000000"),
                ("White", "#ffffff"),
                ("Clear", "#e0e0e0"),
            ],
        },
        {
            "category": "Tough Resin",
            "name": "ABS-Like Resin",
            "brand": "Elegoo",
            "density": 1.12,
            "cost_per_kg": 45.0,
            "surcharge": 5.0,
            "colors": [
                ("Grey", "#808080"),
                ("Black", "#000000"),
            ],
        },
    ]

    for mat_data in material_data:
        category = categories.get(mat_data["category"])
        if not category:
            continue

        # Refresh category to get its ID
        await session.refresh(category)

        result = await session.execute(
            select(Material).where(
                Material.category_id == category.id,
                Material.name == mat_data["name"],
            )
        )
        material = result.scalar_one_or_none()

        if not material:
            material = Material(
                category_id=category.id,
                name=mat_data["name"],
                brand=mat_data["brand"],
                density_g_cm3=mat_data["density"],
                cost_per_kg=mat_data["cost_per_kg"],
                surcharge=mat_data.get("surcharge", 0.0),
                is_active=True,
            )
            session.add(material)
            await session.flush()

            # Add colors
            for color_name, hex_code in mat_data["colors"]:
                color = MaterialColor(
                    material_id=material.id,
                    name=color_name,
                    hex_code=hex_code,
                    is_active=True,
                )
                session.add(color)

        materials[mat_data["name"]] = material

    await session.flush()
    return materials


async def seed_print_profiles(session: AsyncSession) -> dict[str, PrintProfile]:
    """Create print profiles for each technology."""
    profiles = {}

    profile_data = [
        # FDM Profiles
        {
            "technology": Technology.FDM,
            "name": "Draft (0.3mm)",
            "layer_height_mm": 0.3,
            "infill_percentage": 15,
            "supports_enabled": False,
            "quality_multiplier": 0.8,
            "speed_multiplier": 1.3,
            "description": "Fast printing for prototypes",
        },
        {
            "technology": Technology.FDM,
            "name": "Standard (0.2mm)",
            "layer_height_mm": 0.2,
            "infill_percentage": 20,
            "supports_enabled": False,
            "quality_multiplier": 1.0,
            "speed_multiplier": 1.0,
            "description": "Balanced quality and speed",
        },
        {
            "technology": Technology.FDM,
            "name": "Quality (0.15mm)",
            "layer_height_mm": 0.15,
            "infill_percentage": 25,
            "supports_enabled": False,
            "quality_multiplier": 1.2,
            "speed_multiplier": 0.8,
            "description": "Higher quality finish",
        },
        {
            "technology": Technology.FDM,
            "name": "Fine (0.1mm)",
            "layer_height_mm": 0.1,
            "infill_percentage": 30,
            "supports_enabled": False,
            "quality_multiplier": 1.5,
            "speed_multiplier": 0.6,
            "description": "Fine detail printing",
        },
        {
            "technology": Technology.FDM,
            "name": "Standard + Supports",
            "layer_height_mm": 0.2,
            "infill_percentage": 20,
            "supports_enabled": True,
            "quality_multiplier": 1.15,
            "speed_multiplier": 0.9,
            "description": "Standard with support structures",
        },
        # Resin Profiles
        {
            "technology": Technology.RESIN,
            "name": "Standard (0.05mm)",
            "layer_height_mm": 0.05,
            "infill_percentage": 100,
            "supports_enabled": True,
            "quality_multiplier": 1.0,
            "speed_multiplier": 1.0,
            "description": "Standard resin printing",
        },
        {
            "technology": Technology.RESIN,
            "name": "High Detail (0.025mm)",
            "layer_height_mm": 0.025,
            "infill_percentage": 100,
            "supports_enabled": True,
            "quality_multiplier": 1.5,
            "speed_multiplier": 0.5,
            "description": "High detail for miniatures",
        },
    ]

    for prof_data in profile_data:
        result = await session.execute(
            select(PrintProfile).where(
                PrintProfile.technology == prof_data["technology"],
                PrintProfile.name == prof_data["name"],
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = PrintProfile(
                technology=prof_data["technology"],
                name=prof_data["name"],
                layer_height_mm=prof_data["layer_height_mm"],
                infill_percentage=prof_data["infill_percentage"],
                supports_enabled=prof_data["supports_enabled"],
                quality_multiplier=prof_data["quality_multiplier"],
                speed_multiplier=prof_data["speed_multiplier"],
                description=prof_data["description"],
                is_active=True,
            )
            session.add(profile)

        profiles[prof_data["name"]] = profile

    await session.flush()
    return profiles


async def seed_pricing_rule_set(session: AsyncSession) -> PricingRuleSet:
    """Create default pricing rule set."""
    result = await session.execute(
        select(PricingRuleSet).where(PricingRuleSet.version == "1.0.0")
    )
    rule_set = result.scalar_one_or_none()

    if not rule_set:
        rule_set = PricingRuleSet(
            version="1.0.0",
            name="Default Pricing",
            effective_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
            parameters={
                # Base rates
                "machine_rate_eur_per_hour": {
                    "fdm": 15.0,
                    "resin": 25.0,
                },
                "base_fee_eur": 4.0,
                "post_processing_rate_eur_per_minute": 0.80,
                "setup_time_hours": 0.25,

                # Multipliers
                "risk_multiplier": 1.10,
                "support_multiplier": 1.15,
                "complexity_threshold_cm3": 100,
                "complexity_multiplier": 1.05,

                # Minimums
                "minimum_item_price_eur": 6.0,
                "minimum_order_price_eur": 15.0,

                # Lead time parameters
                "base_lead_time_days": 3,
                "rush_multiplier": 1.5,
            },
            is_active=True,
            created_by="system",
        )
        session.add(rule_set)
        await session.flush()

    return rule_set


async def run_seed() -> None:
    """Run all seed functions."""
    async with async_session_maker() as session:
        try:
            print("Seeding users...")
            users = await seed_users(session)
            print(f"  Created/found {len(users)} users")

            print("Seeding material categories...")
            categories = await seed_material_categories(session)
            print(f"  Created/found {len(categories)} categories")

            print("Seeding materials and colors...")
            materials = await seed_materials(session, categories)
            print(f"  Created/found {len(materials)} materials")

            print("Seeding print profiles...")
            profiles = await seed_print_profiles(session)
            print(f"  Created/found {len(profiles)} profiles")

            print("Seeding pricing rule set...")
            await seed_pricing_rule_set(session)
            print("  Created/found default pricing rule set")

            await session.commit()
            print("\nSeed completed successfully!")
            print("\nDemo accounts:")
            print("  Admin: admin@novaprint.local / admin123")
            print("  Customer: demo@example.com / demo123")

        except Exception as e:
            await session.rollback()
            print(f"Seed failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
