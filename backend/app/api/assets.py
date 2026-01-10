"""
File upload and model assets API endpoints.
"""

import io
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.settings import settings
from app.db.models import MetricsStatus, ModelFile
from app.schemas.quotes import ModelFileResponse
from app.services.metrics import MetricsError, calculate_metrics
from app.services.storage import (
    compute_file_hash,
    get_content_type,
    storage_backend,
    validate_file_extension,
)

router = APIRouter(prefix="/api/assets", tags=["Assets"])


async def process_metrics_background(
    file_id: str,
    content: bytes,
    filename: str,
    db_url: str,
) -> None:
    """
    Background task to calculate model metrics.

    In production, this would use Celery for robust background processing.
    """
    from sqlalchemy import create_engine, update
    from sqlalchemy.orm import sessionmaker

    from app.db.models import MetricsStatus, ModelFile

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        try:
            # Update status to processing
            session.execute(
                update(ModelFile)
                .where(ModelFile.id == file_id)
                .values(metrics_status=MetricsStatus.PROCESSING)
            )
            session.commit()

            # Calculate metrics
            metrics = calculate_metrics(content, filename)

            # Update with results
            session.execute(
                update(ModelFile)
                .where(ModelFile.id == file_id)
                .values(
                    metrics_status=MetricsStatus.COMPLETED,
                    volume_cm3=metrics.volume_cm3,
                    surface_area_cm2=metrics.surface_area_cm2,
                    bounding_box_mm=metrics.bounding_box_mm,
                    is_manifold=metrics.is_manifold,
                    is_watertight=metrics.is_watertight,
                    metrics_error=None,
                )
            )
            session.commit()

        except MetricsError as e:
            session.execute(
                update(ModelFile)
                .where(ModelFile.id == file_id)
                .values(
                    metrics_status=MetricsStatus.FAILED,
                    metrics_error=str(e),
                )
            )
            session.commit()

        except Exception as e:
            session.execute(
                update(ModelFile)
                .where(ModelFile.id == file_id)
                .values(
                    metrics_status=MetricsStatus.FAILED,
                    metrics_error=f"Unexpected error: {str(e)}",
                )
            )
            session.commit()


@router.post("/upload", response_model=ModelFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    file: UploadFile,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> ModelFile:
    """
    Upload a 3D model file (STL or 3MF).

    The file will be validated and metrics will be calculated asynchronously.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported: {', '.join(settings.allowed_extensions)}",
        )

    # Read content
    content = await file.read()

    # Check file size
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    # Check for empty file
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    # Compute hash
    file_hash = compute_file_hash(content)

    # Get content type
    content_type = get_content_type(file.filename)

    # Save file
    stored_path = await storage_backend.save(io.BytesIO(content), file.filename)

    # Create database record
    model_file = ModelFile(
        user_id=current_user.id,
        original_filename=file.filename,
        stored_filename=Path(stored_path).name,
        file_path=stored_path,
        file_size_bytes=len(content),
        content_type=content_type,
        sha256_hash=file_hash,
        metrics_status=MetricsStatus.PENDING,
    )
    db.add(model_file)
    await db.flush()
    await db.refresh(model_file)

    # Queue metrics calculation
    background_tasks.add_task(
        process_metrics_background,
        model_file.id,
        content,
        file.filename,
        settings.database_url_sync,
    )

    return model_file


@router.get("/{asset_id}", response_model=ModelFileResponse)
async def get_asset(
    asset_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> ModelFile:
    """Get model file metadata and metrics."""
    result = await db.execute(
        select(ModelFile).where(
            ModelFile.id == asset_id,
            ModelFile.user_id == current_user.id,
        )
    )
    model_file = result.scalar_one_or_none()

    if not model_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    return model_file


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> StreamingResponse:
    """Download the original model file."""
    result = await db.execute(
        select(ModelFile).where(
            ModelFile.id == asset_id,
            ModelFile.user_id == current_user.id,
        )
    )
    model_file = result.scalar_one_or_none()

    if not model_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    try:
        content = await storage_backend.get(model_file.file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )

    return StreamingResponse(
        io.BytesIO(content),
        media_type=model_file.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{model_file.original_filename}"'
        },
    )


@router.post("/{asset_id}/recalculate-metrics", response_model=ModelFileResponse)
async def recalculate_metrics(
    asset_id: str,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> ModelFile:
    """
    Trigger recalculation of model metrics.

    Useful if initial calculation failed or timed out.
    """
    result = await db.execute(
        select(ModelFile).where(
            ModelFile.id == asset_id,
            ModelFile.user_id == current_user.id,
        )
    )
    model_file = result.scalar_one_or_none()

    if not model_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Get file content
    try:
        content = await storage_backend.get(model_file.file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found in storage",
        )

    # Reset status
    model_file.metrics_status = MetricsStatus.PENDING
    model_file.metrics_error = None
    await db.flush()

    # Queue recalculation
    background_tasks.add_task(
        process_metrics_background,
        model_file.id,
        content,
        model_file.original_filename,
        settings.database_url_sync,
    )

    await db.refresh(model_file)
    return model_file


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a model file."""
    result = await db.execute(
        select(ModelFile).where(
            ModelFile.id == asset_id,
            ModelFile.user_id == current_user.id,
        )
    )
    model_file = result.scalar_one_or_none()

    if not model_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )

    # Delete file from storage
    await storage_backend.delete(model_file.file_path)

    # Delete database record
    await db.delete(model_file)
