"""
Tests for pricing engine.
"""

from datetime import datetime, timezone

import pytest

from app.db.models import Material, MaterialCategory, PricingRuleSet, PrintProfile, Technology
from app.services.pricing import calculate_price, estimate_print_time_hours


class TestEstimatePrintTime:
    """Tests for print time estimation."""

    def test_fdm_print_time_basic(self):
        """Test basic FDM print time estimation."""
        profile = PrintProfile(
            technology=Technology.FDM,
            name="Standard",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=False,
            quality_multiplier=1.0,
            speed_multiplier=1.0,
            is_active=True,
        )

        # 10 cm^3 model
        time_hours = estimate_print_time_hours(10.0, profile, Technology.FDM)

        assert time_hours > 0
        assert time_hours < 24  # Should not take more than a day for small model

    def test_fdm_print_time_larger_model(self):
        """Test that larger models take more time."""
        profile = PrintProfile(
            technology=Technology.FDM,
            name="Standard",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=False,
            quality_multiplier=1.0,
            speed_multiplier=1.0,
            is_active=True,
        )

        time_small = estimate_print_time_hours(10.0, profile, Technology.FDM)
        time_large = estimate_print_time_hours(100.0, profile, Technology.FDM)

        assert time_large > time_small

    def test_quality_multiplier_increases_time(self):
        """Test that higher quality multiplier increases print time."""
        profile_standard = PrintProfile(
            technology=Technology.FDM,
            name="Standard",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=False,
            quality_multiplier=1.0,
            speed_multiplier=1.0,
            is_active=True,
        )

        profile_quality = PrintProfile(
            technology=Technology.FDM,
            name="Quality",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=False,
            quality_multiplier=1.5,
            speed_multiplier=1.0,
            is_active=True,
        )

        time_standard = estimate_print_time_hours(10.0, profile_standard, Technology.FDM)
        time_quality = estimate_print_time_hours(10.0, profile_quality, Technology.FDM)

        assert time_quality > time_standard


class TestCalculatePrice:
    """Tests for price calculation."""

    @pytest.fixture
    def material(self):
        """Create a test material."""
        category = MaterialCategory(
            id=1,
            name="PLA",
            technology=Technology.FDM,
            is_active=True,
        )
        return Material(
            id=1,
            category_id=1,
            category=category,
            name="PLA Standard",
            brand="TestBrand",
            density_g_cm3=1.24,
            cost_per_kg=25.0,
            surcharge=0.0,
            is_active=True,
        )

    @pytest.fixture
    def profile(self):
        """Create a test print profile."""
        return PrintProfile(
            id=1,
            technology=Technology.FDM,
            name="Standard",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=False,
            quality_multiplier=1.0,
            speed_multiplier=1.0,
            is_active=True,
        )

    @pytest.fixture
    def rule_set(self):
        """Create a test pricing rule set."""
        return PricingRuleSet(
            id=1,
            version="1.0.0",
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

    def test_basic_price_calculation(self, material, profile, rule_set):
        """Test basic price calculation."""
        breakdown = calculate_price(
            volume_cm3=10.0,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=1,
        )

        assert breakdown.material_cost > 0
        assert breakdown.machine_cost > 0
        assert breakdown.handling_fee == 4.0
        assert breakdown.unit_price > 0
        assert breakdown.total_price > 0
        assert breakdown.lead_time_days >= 3

    def test_quantity_affects_total(self, material, profile, rule_set):
        """Test that quantity affects total price."""
        breakdown_1 = calculate_price(
            volume_cm3=10.0,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=1,
        )

        breakdown_3 = calculate_price(
            volume_cm3=10.0,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=3,
        )

        assert breakdown_3.total_price > breakdown_1.total_price
        assert breakdown_3.unit_price == breakdown_1.unit_price

    def test_minimum_price_applied(self, material, profile, rule_set):
        """Test that minimum prices are applied."""
        # Very small volume should trigger minimum
        breakdown = calculate_price(
            volume_cm3=0.1,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=1,
        )

        assert breakdown.minimum_applied is True
        assert breakdown.unit_price >= 6.0
        assert breakdown.total_price >= 15.0

    def test_larger_volume_higher_price(self, material, profile, rule_set):
        """Test that larger volumes result in higher prices."""
        small = calculate_price(
            volume_cm3=10.0,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=1,
        )

        large = calculate_price(
            volume_cm3=100.0,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=1,
        )

        assert large.total_price > small.total_price
        assert large.material_cost > small.material_cost
        assert large.machine_cost > small.machine_cost

    def test_supports_add_cost(self, material, rule_set):
        """Test that supports add cost."""
        profile_no_supports = PrintProfile(
            id=1,
            technology=Technology.FDM,
            name="Standard",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=False,
            quality_multiplier=1.0,
            speed_multiplier=1.0,
            is_active=True,
        )

        profile_with_supports = PrintProfile(
            id=2,
            technology=Technology.FDM,
            name="Standard + Supports",
            layer_height_mm=0.2,
            infill_percentage=20,
            supports_enabled=True,
            quality_multiplier=1.0,
            speed_multiplier=1.0,
            is_active=True,
        )

        price_no_supports = calculate_price(
            volume_cm3=50.0,
            material=material,
            profile=profile_no_supports,
            rule_set=rule_set,
            quantity=1,
        )

        price_with_supports = calculate_price(
            volume_cm3=50.0,
            material=material,
            profile=profile_with_supports,
            rule_set=rule_set,
            quantity=1,
        )

        assert price_with_supports.support_cost > 0
        assert price_with_supports.total_price > price_no_supports.total_price

    def test_breakdown_snapshot_is_complete(self, material, profile, rule_set):
        """Test that all breakdown fields are populated."""
        breakdown = calculate_price(
            volume_cm3=10.0,
            material=material,
            profile=profile,
            rule_set=rule_set,
            quantity=1,
        )

        assert isinstance(breakdown.material_cost, float)
        assert isinstance(breakdown.machine_cost, float)
        assert isinstance(breakdown.handling_fee, float)
        assert isinstance(breakdown.support_cost, float)
        assert isinstance(breakdown.quality_multiplier_applied, float)
        assert isinstance(breakdown.risk_multiplier_applied, float)
        assert isinstance(breakdown.subtotal, float)
        assert isinstance(breakdown.minimum_applied, bool)
        assert isinstance(breakdown.unit_price, float)
        assert isinstance(breakdown.total_price, float)
        assert isinstance(breakdown.lead_time_days, int)
