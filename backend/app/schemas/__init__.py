"""
AVENZO Backend — Schemas Package
Exports all Phase 1 and Phase 2 Pydantic Request and Response models.
"""

from app.schemas.common import ApiResponse, PaginationMeta, ErrorDetail
from app.schemas.user import UserRead, UserUpdate, RoleRead
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate, BrandRead
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate, WarehouseLocationCreate, WarehouseLocationRead
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.schemas.batch import BatchCreate, BatchRead, BatchUpdate
from app.schemas.inventory import InventoryRead, InventoryAdjustRequest, InventoryTransactionRead
from app.schemas.fefo import (
    FEFORankedBatchRead,
    FEFOAllocationRequest,
    FEFOBatchAllocationItem,
    FEFOAllocationPlanResponse,
    FEFOVerificationRequest,
    FEFOVerificationResponse,
)
from app.schemas.expiry import ExpirySummaryResponse, InventoryRiskMetricsResponse

__all__ = [
    "ApiResponse",
    "PaginationMeta",
    "ErrorDetail",
    "UserRead",
    "UserUpdate",
    "RoleRead",
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "CategoryCreate",
    "CategoryRead",
    "CategoryUpdate",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "BrandRead",
    "WarehouseCreate",
    "WarehouseRead",
    "WarehouseUpdate",
    "WarehouseLocationCreate",
    "WarehouseLocationRead",
    "SupplierCreate",
    "SupplierRead",
    "SupplierUpdate",
    "BatchCreate",
    "BatchRead",
    "BatchUpdate",
    "InventoryRead",
    "InventoryAdjustRequest",
    "InventoryTransactionRead",
    "FEFORankedBatchRead",
    "FEFOAllocationRequest",
    "FEFOBatchAllocationItem",
    "FEFOAllocationPlanResponse",
    "FEFOVerificationRequest",
    "FEFOVerificationResponse",
    "ExpirySummaryResponse",
    "InventoryRiskMetricsResponse",
]
