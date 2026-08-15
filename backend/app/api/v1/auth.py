"""
AVENZO Backend — Authentication API Router (/api/v1/auth)
Register, Login, Token Refresh, and Current User Profile.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.user import UserRead
from app.schemas.common import ApiResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, session: AsyncSession = Depends(get_db)):
    """
    Self-registration endpoint for Consumers and Staff.
    """
    user = await auth_service.register_user(session, request)
    return ApiResponse(
        success=True,
        data=UserRead.model_validate(user),
        message="User registered successfully.",
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(request: LoginRequest, session: AsyncSession = Depends(get_db)):
    """
    Authenticate credentials and issue JWT access and refresh tokens.
    """
    user, access_token, refresh_token = await auth_service.authenticate_user(session, request)
    return ApiResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        ),
        message="Login successful.",
    )


@router.post("/refresh", response_model=ApiResponse[dict])
async def refresh_token(request: RefreshRequest, session: AsyncSession = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    """
    new_token, user = await auth_service.refresh_access_token(session, request.refresh_token)
    return ApiResponse(
        success=True,
        data={"access_token": new_token, "token_type": "bearer"},
        message="Access token refreshed successfully.",
    )


@router.get("/me", response_model=ApiResponse[UserRead])
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get profile details of current authenticated user.
    """
    return ApiResponse(
        success=True,
        data=UserRead.model_validate(current_user),
    )
