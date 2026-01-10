"""
API integration tests.
"""

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token
from app.db.models import User


class TestHealthCheck:
    """Health check endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuth:
    """Authentication endpoint tests."""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "name": "New User",
                "password": "password123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert data["role"] == "customer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "name": "Another User",
                "password": "password123",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user: User):
        """Test login with invalid password."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, test_user: User):
        """Test getting current user info."""
        token = create_access_token({"sub": test_user.id})
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401


class TestMaterials:
    """Materials endpoint tests."""

    @pytest.mark.asyncio
    async def test_list_technologies(self, client: AsyncClient):
        """Test listing technologies."""
        response = await client.get("/api/technologies")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(t["id"] == "fdm" for t in data)
        assert any(t["id"] == "resin" for t in data)

    @pytest.mark.asyncio
    async def test_list_materials(self, client: AsyncClient, test_material):
        """Test listing materials."""
        response = await client.get("/api/materials")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "PLA Standard"

    @pytest.mark.asyncio
    async def test_list_materials_filter_by_technology(self, client: AsyncClient, test_material):
        """Test filtering materials by technology."""
        response = await client.get("/api/materials?technology=fdm")
        assert response.status_code == 200
        data = response.json()
        assert all(m["technology"] == "fdm" for m in data)

    @pytest.mark.asyncio
    async def test_get_material(self, client: AsyncClient, test_material):
        """Test getting a specific material."""
        response = await client.get(f"/api/materials/{test_material.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_material.id
        assert data["name"] == test_material.name

    @pytest.mark.asyncio
    async def test_get_material_not_found(self, client: AsyncClient):
        """Test getting non-existent material."""
        response = await client.get("/api/materials/99999")
        assert response.status_code == 404


class TestProfiles:
    """Print profiles endpoint tests."""

    @pytest.mark.asyncio
    async def test_list_profiles(self, client: AsyncClient, test_profile):
        """Test listing print profiles."""
        response = await client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_profiles_filter_by_technology(self, client: AsyncClient, test_profile):
        """Test filtering profiles by technology."""
        response = await client.get("/api/profiles?technology=fdm")
        assert response.status_code == 200
        data = response.json()
        assert all(p["technology"] == "fdm" for p in data)

    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, test_profile):
        """Test getting a specific profile."""
        response = await client.get(f"/api/profiles/{test_profile.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_profile.id
        assert data["name"] == test_profile.name


class TestAdmin:
    """Admin endpoint tests."""

    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_auth(self, client: AsyncClient):
        """Test that admin endpoints require authentication."""
        response = await client.get("/api/admin/orders")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_endpoint_requires_admin_role(
        self, client: AsyncClient, test_user: User
    ):
        """Test that admin endpoints require admin role."""
        token = create_access_token({"sub": test_user.id})
        response = await client.get(
            "/api/admin/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_list_orders(self, client: AsyncClient, admin_user: User):
        """Test admin listing orders."""
        token = create_access_token({"sub": admin_user.id})
        response = await client.get(
            "/api/admin/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_admin_get_analytics(self, client: AsyncClient, admin_user: User):
        """Test admin getting analytics."""
        token = create_access_token({"sub": admin_user.id})
        response = await client.get(
            "/api/admin/analytics/summary",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "orders_7d" in data
        assert "revenue_7d" in data

    @pytest.mark.asyncio
    async def test_admin_list_pricing_configs(self, client: AsyncClient, admin_user: User, test_pricing_rule_set):
        """Test admin listing pricing configurations."""
        token = create_access_token({"sub": admin_user.id})
        response = await client.get(
            "/api/admin/pricing",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
