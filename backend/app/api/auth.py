"""
Authentication API endpoints.
"""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.settings import settings
from app.db.models import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: DbSession) -> User:
    """Register a new user account."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        role=UserRole.CUSTOMER,
        company_name=request.company_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: DbSession) -> TokenResponse:
    """Authenticate and get access token."""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> User:
    """Get current user information."""
    return current_user


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(request: PasswordResetRequest, db: DbSession) -> dict:
    """
    Request a password reset.

    Note: In production, this would send an email with a reset link.
    For demo purposes, this just returns a success message.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Always return success to prevent email enumeration
    if user:
        # In production: generate reset token and send email
        # token = create_password_reset_token(user.id)
        # await send_reset_email(user.email, token)
        pass

    return {"message": "If the email exists, a reset link will be sent"}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(request: PasswordResetConfirm, db: DbSession) -> dict:
    """
    Confirm password reset with token.

    Note: In production, this would validate the reset token.
    For demo purposes, this is a placeholder.
    """
    # In production: validate token and get user_id
    # user_id = validate_reset_token(request.token)
    # user = await db.get(User, user_id)
    # user.password_hash = get_password_hash(request.new_password)

    return {"message": "Password reset functionality is mocked for demo"}
