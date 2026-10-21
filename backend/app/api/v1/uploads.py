"""
AVENZO Backend — Media & Image Uploads API Router (/api/v1/uploads)
Provides endpoints for validating and uploading product images and category icons to Cloudinary.
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.services import image_service

router = APIRouter(prefix="/uploads", tags=["Media & Image Uploads"])


@router.post("/image", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def upload_image_endpoint(
    file: UploadFile = File(...),
    folder: Optional[str] = Query(None, description="Optional target folder in Cloudinary (e.g. 'avenzo/products')"),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Upload an image for a product or category to Cloudinary.
    Enforces maximum 5 MB file size, checks file signature (JPEG, PNG, WebP),
    validates dimensions (<= 4096px, <= 16.7 MP), and returns HTTPS secure_url and public_id.
    Requires ADMIN or BUSINESS_MANAGER role.
    """
    result = await image_service.upload_image_to_cloudinary(file, folder=folder)
    return ApiResponse(
        success=True,
        data=result,
        message="Image uploaded successfully.",
    )
