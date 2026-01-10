"""
Test configuration and fixtures.
"""

import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import get_password_hash
from app.db.database import Base, get_db
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
from app.main import app

# Test database URL (use SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_maker() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=get_password_hash("password123"),
        role=UserRole.CUSTOMER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        email="admin@example.com",
        name="Admin User",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_material(db_session: AsyncSession) -> Material:
    """Create a test material with colors."""
    category = MaterialCategory(
        name="PLA",
        technology=Technology.FDM,
        description="Test PLA",
        is_active=True,
    )
    db_session.add(category)
    await db_session.flush()

    material = Material(
        category_id=category.id,
        name="PLA Standard",
        brand="TestBrand",
        density_g_cm3=1.24,
        cost_per_kg=25.0,
        surcharge=0.0,
        is_active=True,
    )
    db_session.add(material)
    await db_session.flush()

    color = MaterialColor(
        material_id=material.id,
        name="Black",
        hex_code="#000000",
        is_active=True,
    )
    db_session.add(color)
    await db_session.commit()
    await db_session.refresh(material)
    return material


@pytest_asyncio.fixture
async def test_profile(db_session: AsyncSession) -> PrintProfile:
    """Create a test print profile."""
    profile = PrintProfile(
        technology=Technology.FDM,
        name="Standard (0.2mm)",
        layer_height_mm=0.2,
        infill_percentage=20,
        supports_enabled=False,
        quality_multiplier=1.0,
        speed_multiplier=1.0,
        is_active=True,
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    return profile


@pytest_asyncio.fixture
async def test_pricing_rule_set(db_session: AsyncSession) -> PricingRuleSet:
    """Create a test pricing rule set."""
    rule_set = PricingRuleSet(
        version="1.0.0-test",
        name="Test Pricing",
        effective_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        parameters={
            "machine_rate_eur_per_hour": {"fdm": 15.0, "resin": 25.0},
            "base_fee_eur": 4.0,
            "post_processing_rate_eur_per_minute": 0.80,
            "setup_time_hours": 0.25,
            "risk_multiplier": 1.10,
            "support_multiplier": 1.15,
            "complexity_threshold_cm3": 100,
            "complexity_multiplier": 1.05,
            "minimum_item_price_eur": 6.0,
            "minimum_order_price_eur": 15.0,
            "base_lead_time_days": 3,
        },
        is_active=True,
        created_by="test",
    )
    db_session.add(rule_set)
    await db_session.commit()
    await db_session.refresh(rule_set)
    return rule_set
