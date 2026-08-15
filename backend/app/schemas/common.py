"""
AVENZO Backend — Common Response Schemas
Standardized API Envelope and Pagination models.
"""

from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class PaginationMeta(BaseModel):
    page: int = Field(..., example=1)
    per_page: int = Field(..., example=20)
    total: int = Field(..., example=100)
    total_pages: int = Field(..., example=5)
    has_next: bool = Field(..., example=True)
    has_prev: bool = Field(..., example=False)


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[ErrorDetail] = None
    meta: Optional[PaginationMeta] = None
