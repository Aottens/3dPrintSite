"""
Materials and print profiles API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import DbSession
from app.db.models import Material, MaterialCategory, MaterialColor, PrintProfile, Technology
from app.schemas.materials import (
    MaterialCategoryResponse,
    MaterialColorResponse,
    MaterialResponse,
    PrintProfileResponse,
)

router = APIRouter(prefix="/api", tags=["Materials & Profiles"])


@router.get("/technologies")
async def list_technologies() -> list[dict]:
    """List available 3D printing technologies."""
    return [
        {"id": "fdm", "name": "FDM", "description": "Fused Deposition Modeling"},
        {"id": "resin", "name": "Resin", "description": "Stereolithography / MSLA"},
    ]


@router.get("/materials/categories", response_model=list[MaterialCategoryResponse])
async def list_material_categories(
    db: DbSession,
    technology: str | None = Query(None, pattern=r"^(fdm|resin)$"),
) -> list[MaterialCategory]:
    """List material categories, optionally filtered by technology."""
    query = select(MaterialCategory).where(MaterialCategory.is_active == True)

    if technology:
        query = query.where(MaterialCategory.technology == Technology(technology))

    result = await db.execute(query.order_by(MaterialCategory.name))
    return list(result.scalars().all())


@router.get("/materials", response_model=list[MaterialResponse])
async def list_materials(
    db: DbSession,
    technology: str | None = Query(None, pattern=r"^(fdm|resin)$"),
    category_id: int | None = None,
    active_only: bool = True,
) -> list[dict]:
    """
    List materials with their colors.

    Optionally filter by technology or category.
    """
    query = (
        select(Material)
        .options(selectinload(Material.colors), selectinload(Material.category))
    )

    if active_only:
        query = query.where(Material.is_active == True)

    if category_id:
        query = query.where(Material.category_id == category_id)

    if technology:
        query = query.join(MaterialCategory).where(
            MaterialCategory.technology == Technology(technology)
        )

    result = await db.execute(query.order_by(Material.name))
    materials = result.scalars().all()

    # Transform to response format
    return [
        {
            "id": m.id,
            "category_id": m.category_id,
            "category_name": m.category.name,
            "technology": m.category.technology.value,
            "name": m.name,
            "brand": m.brand,
            "density_g_cm3": m.density_g_cm3,
            "cost_per_kg": m.cost_per_kg,
            "surcharge": m.surcharge,
            "is_active": m.is_active,
            "colors": [
                MaterialColorResponse(
                    id=c.id,
                    name=c.name,
                    hex_code=c.hex_code,
                    is_active=c.is_active,
                )
                for c in m.colors
                if c.is_active or not active_only
            ],
        }
        for m in materials
    ]


@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(material_id: int, db: DbSession) -> dict:
    """Get a specific material by ID."""
    query = (
        select(Material)
        .options(selectinload(Material.colors), selectinload(Material.category))
        .where(Material.id == material_id)
    )
    result = await db.execute(query)
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

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
            MaterialColorResponse(
                id=c.id,
                name=c.name,
                hex_code=c.hex_code,
                is_active=c.is_active,
            )
            for c in material.colors
        ],
    }


@router.get("/materials/{material_id}/colors", response_model=list[MaterialColorResponse])
async def list_material_colors(
    material_id: int,
    db: DbSession,
    active_only: bool = True,
) -> list[MaterialColor]:
    """List available colors for a material."""
    query = select(MaterialColor).where(MaterialColor.material_id == material_id)

    if active_only:
        query = query.where(MaterialColor.is_active == True)

    result = await db.execute(query.order_by(MaterialColor.name))
    return list(result.scalars().all())


@router.get("/profiles", response_model=list[PrintProfileResponse])
async def list_profiles(
    db: DbSession,
    technology: str | None = Query(None, pattern=r"^(fdm|resin)$"),
    active_only: bool = True,
) -> list[PrintProfile]:
    """
    List print profiles.

    Optionally filter by technology.
    """
    query = select(PrintProfile)

    if active_only:
        query = query.where(PrintProfile.is_active == True)

    if technology:
        query = query.where(PrintProfile.technology == Technology(technology))

    result = await db.execute(query.order_by(PrintProfile.layer_height_mm))
    return list(result.scalars().all())


@router.get("/profiles/{profile_id}", response_model=PrintProfileResponse)
async def get_profile(profile_id: int, db: DbSession) -> PrintProfile:
    """Get a specific print profile by ID."""
    result = await db.execute(
        select(PrintProfile).where(PrintProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return profile
