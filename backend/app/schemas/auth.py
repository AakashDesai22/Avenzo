"""
AVENZO Backend — Authentication Pydantic Schemas
Register, Login, Token, and User Profile request/response models.
"""

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: str = Field(default="consumer", pattern="^(business|consumer)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class RefreshRequest(BaseModel):
    refresh_token: str
