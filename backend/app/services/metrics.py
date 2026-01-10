"""
3D Model metrics calculation service using trimesh.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

import numpy as np

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


@dataclass
class ModelMetrics:
    """Calculated metrics for a 3D model."""

    volume_cm3: float
    surface_area_cm2: float
    bounding_box_mm: dict[str, float]  # x, y, z dimensions
    is_manifold: bool
    is_watertight: bool


class MetricsError(Exception):
    """Error during metrics calculation."""

    pass


def _load_mesh_from_stl(content: bytes) -> "trimesh.Trimesh":
    """Load a mesh from STL content."""
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
        f.write(content)
        f.flush()
        mesh = trimesh.load(f.name, file_type="stl")
        Path(f.name).unlink()
    return mesh


def _load_mesh_from_3mf(content: bytes) -> "trimesh.Trimesh":
    """Load a mesh from 3MF content."""
    with tempfile.NamedTemporaryFile(suffix=".3mf", delete=False) as f:
        f.write(content)
        f.flush()

        # 3MF is a ZIP archive containing model data
        try:
            meshes = []
            with ZipFile(f.name, "r") as zf:
                # Find the model file
                for name in zf.namelist():
                    if name.endswith(".model") or "3D/3dmodel.model" in name:
                        # Extract and load
                        model_content = zf.read(name)
                        with tempfile.NamedTemporaryFile(
                            suffix=".model", delete=False
                        ) as mf:
                            mf.write(model_content)
                            mf.flush()
                            mesh = trimesh.load(mf.name)
                            if isinstance(mesh, trimesh.Scene):
                                meshes.extend(mesh.geometry.values())
                            else:
                                meshes.append(mesh)
                            Path(mf.name).unlink()

            if not meshes:
                # Try loading directly as trimesh handles some 3mf variants
                mesh = trimesh.load(f.name)
                if isinstance(mesh, trimesh.Scene):
                    meshes = list(mesh.geometry.values())
                else:
                    meshes = [mesh]

            # Concatenate all meshes
            if len(meshes) == 1:
                result = meshes[0]
            else:
                result = trimesh.util.concatenate(meshes)

        finally:
            Path(f.name).unlink()

    return result


def calculate_metrics(content: bytes, filename: str) -> ModelMetrics:
    """
    Calculate metrics for a 3D model file.

    Args:
        content: File content as bytes
        filename: Original filename to determine file type

    Returns:
        ModelMetrics with calculated values

    Raises:
        MetricsError: If calculation fails
    """
    if not TRIMESH_AVAILABLE:
        raise MetricsError("trimesh library not available")

    ext = Path(filename).suffix.lower()

    try:
        if ext == ".stl":
            mesh = _load_mesh_from_stl(content)
        elif ext == ".3mf":
            mesh = _load_mesh_from_3mf(content)
        else:
            raise MetricsError(f"Unsupported file type: {ext}")

        # Handle Scene objects (multiple meshes)
        if isinstance(mesh, trimesh.Scene):
            if len(mesh.geometry) == 0:
                raise MetricsError("Empty mesh - no geometry found")
            # Combine all meshes
            meshes = list(mesh.geometry.values())
            mesh = trimesh.util.concatenate(meshes)

        # Ensure we have a valid mesh
        if not isinstance(mesh, trimesh.Trimesh):
            raise MetricsError("Failed to load mesh geometry")

        if len(mesh.vertices) == 0:
            raise MetricsError("Empty mesh - no vertices found")

        # Calculate volume in mm^3, convert to cm^3
        # STL files are typically in mm
        try:
            volume_mm3 = abs(mesh.volume)
        except Exception:
            volume_mm3 = abs(mesh.convex_hull.volume)

        volume_cm3 = volume_mm3 / 1000.0

        # Calculate surface area in mm^2, convert to cm^2
        surface_area_mm2 = mesh.area
        surface_area_cm2 = surface_area_mm2 / 100.0

        # Calculate bounding box
        bounds = mesh.bounds
        bounding_box_mm = {
            "x": float(bounds[1][0] - bounds[0][0]),
            "y": float(bounds[1][1] - bounds[0][1]),
            "z": float(bounds[1][2] - bounds[0][2]),
        }

        # Check mesh properties
        is_watertight = mesh.is_watertight
        is_manifold = mesh.is_watertight  # In trimesh, watertight implies manifold

        return ModelMetrics(
            volume_cm3=round(volume_cm3, 4),
            surface_area_cm2=round(surface_area_cm2, 4),
            bounding_box_mm=bounding_box_mm,
            is_manifold=is_manifold,
            is_watertight=is_watertight,
        )

    except MetricsError:
        raise
    except Exception as e:
        raise MetricsError(f"Failed to calculate metrics: {str(e)}")


async def process_model_metrics_async(
    file_id: str,
    content: bytes,
    filename: str,
) -> ModelMetrics:
    """
    Async wrapper for metrics calculation.

    In production, this could be run as a background task with Celery.
    """
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        calculate_metrics,
        content,
        filename,
    )
