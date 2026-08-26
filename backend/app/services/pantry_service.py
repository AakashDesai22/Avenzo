"""
AVENZO Backend — Consumer Digital Pantry Service
Business logic for managing consumer pantries, pantry items, consumption/discard actions,
and strict consumer data ownership isolation.
"""

from typing import List, Optional
from uuid import UUID
from datetime import timedelta, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.product import Product
from app.models.inventory import Batch
from app.schemas.pantry import PantryItemCreate, PantryItemUpdate, PantryItemRead
from app.services.expiry_service import calculate_dte, classify_expiry_status


async def get_or_create_default_pantry(session: AsyncSession, user_id: UUID) -> ConsumerPantry:
    """Retrieves existing default pantry for user or creates one."""
    res = await session.execute(
        select(ConsumerPantry).where(ConsumerPantry.user_id == user_id, ConsumerPantry.is_default == True)
    )
    pantry = res.scalars().first()
    if not pantry:
        pantry = ConsumerPantry(
            user_id=user_id,
            name="My Home Pantry",
            is_default=True,
        )
        session.add(pantry)
        await session.commit()
        await session.refresh(pantry)
    return pantry


async def get_pantry_item(session: AsyncSession, user_id: UUID, item_id: UUID) -> PantryItem:
    """
    Retrieves pantry item ensuring strict consumer ownership isolation.
    If item does not exist or belongs to another user, raises 404.
    """
    stmt = (
        select(PantryItem)
        .options(
            joinedload(PantryItem.pantry),
            joinedload(PantryItem.product).joinedload(Product.category),
            joinedload(PantryItem.product).joinedload(Product.brand),
            joinedload(PantryItem.batch),
        )
        .join(ConsumerPantry)
        .where(
            PantryItem.id == item_id,
            PantryItem.is_deleted == False,
            ConsumerPantry.user_id == user_id,
        )
    )
    res = await session.execute(stmt)
    item = res.scalars().first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pantry item not found.",
        )
    return item


def _enrich_item_read(item: PantryItem) -> PantryItemRead:
    """Enriches PantryItem model into PantryItemRead DTO with derived DTE, status, and batch number."""
    has_exp = True
    if item.product and not item.product.has_expiry:
        has_exp = False

    dte = calculate_dte(item.expiry_date)
    exp_status = classify_expiry_status(item.expiry_date, has_expiry=has_exp)

    dto = PantryItemRead.model_validate(item)
    dto.days_to_expiry = dte
    dto.expiry_status = exp_status
    if item.batch and not dto.batch_number:
        dto.batch_number = item.batch.batch_number
    return dto


async def list_recalled_pantry_items(session: AsyncSession, user_id: UUID) -> List[PantryItemRead]:
    """Lists consumer's pantry items marked as recalled (is_recalled == True)."""
    stmt = (
        select(PantryItem)
        .options(
            joinedload(PantryItem.product).joinedload(Product.category),
            joinedload(PantryItem.product).joinedload(Product.brand),
            joinedload(PantryItem.batch),
        )
        .join(ConsumerPantry)
        .where(
            ConsumerPantry.user_id == user_id,
            PantryItem.is_deleted == False,
            PantryItem.is_recalled == True,
        )
        .order_by(PantryItem.recalled_at.desc().nulls_last())
    )

    res = await session.execute(stmt)
    items = res.scalars().unique().all()
    return [_enrich_item_read(item) for item in items]


async def create_pantry_item(
    session: AsyncSession, user_id: UUID, data: PantryItemCreate
) -> PantryItemRead:
    """Creates a new item in consumer pantry with atomic log insertion and ownership checks."""
    # Resolve Pantry
    if data.pantry_id:
        pantry_res = await session.execute(
            select(ConsumerPantry).where(ConsumerPantry.id == data.pantry_id, ConsumerPantry.user_id == user_id)
        )
        pantry = pantry_res.scalars().first()
        if not pantry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target pantry not found or access forbidden.",
            )
    else:
        pantry = await get_or_create_default_pantry(session, user_id)

    # Validate Product if supplied
    product: Optional[Product] = None
    if data.product_id:
        prod_res = await session.execute(
            select(Product).where(Product.id == data.product_id, Product.is_deleted == False)
        )
        product = prod_res.scalars().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id '{data.product_id}' not found.",
            )

    # Validate Batch if supplied
    batch: Optional[Batch] = None
    if data.batch_id:
        batch_res = await session.execute(
            select(Batch).where(Batch.id == data.batch_id)
        )
        batch = batch_res.scalars().first()
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id '{data.batch_id}' not found.",
            )

    # Resolve Expiry Date Hierarchy
    resolved_expiry: Optional[date] = data.expiry_date
    if not resolved_expiry and batch and batch.expiry_date:
        resolved_expiry = batch.expiry_date
    elif not resolved_expiry and product and product.shelf_life_days and data.purchase_date:
        resolved_expiry = data.purchase_date + timedelta(days=product.shelf_life_days)

    item = PantryItem(
        pantry_id=pantry.id,
        product_id=product.id if product else None,
        batch_id=batch.id if batch else None,
        custom_name=data.custom_name,
        barcode=data.barcode or (product.barcode if product else None),
        quantity=data.quantity,
        unit=data.unit,
        purchase_date=data.purchase_date,
        expiry_date=resolved_expiry,
        storage_location=data.storage_location,
        status="active",
        notes=data.notes,
    )
    session.add(item)
    await session.flush()

    # Create immutable audit log
    log = PantryItemLog(
        pantry_item_id=item.id,
        action="ADDED",
        quantity_change=data.quantity,
    )
    session.add(log)

    await session.commit()
    loaded_item = await get_pantry_item(session, user_id, item.id)
    return _enrich_item_read(loaded_item)


async def list_pantry_items(
    session: AsyncSession,
    user_id: UUID,
    pantry_id: Optional[UUID] = None,
    storage_location: Optional[str] = None,
    status_filter: str = "active",
) -> List[PantryItemRead]:
    """Lists active pantry items for user with ownership filtering."""
    stmt = (
        select(PantryItem)
        .options(
            joinedload(PantryItem.product).joinedload(Product.category),
            joinedload(PantryItem.product).joinedload(Product.brand),
            joinedload(PantryItem.batch),
        )
        .join(ConsumerPantry)
        .where(
            ConsumerPantry.user_id == user_id,
            PantryItem.is_deleted == False,
        )
    )

    if pantry_id:
        stmt = stmt.where(PantryItem.pantry_id == pantry_id)

    if storage_location:
        stmt = stmt.where(PantryItem.storage_location == storage_location)

    if status_filter:
        stmt = stmt.where(PantryItem.status == status_filter)

    stmt = stmt.order_by(PantryItem.created_at.desc())

    res = await session.execute(stmt)
    items = res.scalars().unique().all()
    return [_enrich_item_read(item) for item in items]


async def update_pantry_item(
    session: AsyncSession, user_id: UUID, item_id: UUID, data: PantryItemUpdate
) -> PantryItemRead:
    """Updates pantry item with quantity change logging."""
    item = await get_pantry_item(session, user_id, item_id)

    update_dict = data.model_dump(exclude_unset=True)

    if "quantity" in update_dict and update_dict["quantity"] is not None:
        new_qty = Decimal(str(update_dict["quantity"]))
        diff = new_qty - Decimal(str(item.quantity))
        if diff != Decimal("0"):
            log = PantryItemLog(
                pantry_item_id=item.id,
                action="QUANTITY_ADJUSTED",
                quantity_change=diff,
            )
            session.add(log)
            item.quantity = new_qty

    for key, value in update_dict.items():
        if key != "quantity":
            setattr(item, key, value)

    await session.commit()
    loaded_item = await get_pantry_item(session, user_id, item.id)
    return _enrich_item_read(loaded_item)


async def consume_pantry_item(
    session: AsyncSession, user_id: UUID, item_id: UUID, consume_qty: Decimal
) -> PantryItemRead:
    """Consumes quantity from item atomically."""
    item = await get_pantry_item(session, user_id, item_id)

    if consume_qty <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consume quantity must be greater than zero.",
        )

    current_qty = Decimal(str(item.quantity))
    if consume_qty > current_qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot consume {consume_qty} {item.unit}. Available stock is {current_qty} {item.unit}.",
        )

    item.quantity = current_qty - consume_qty
    if item.quantity == Decimal("0"):
        item.status = "consumed"

    log = PantryItemLog(
        pantry_item_id=item.id,
        action="CONSUMED",
        quantity_change=-consume_qty,
    )
    session.add(log)

    await session.commit()
    loaded_item = await get_pantry_item(session, user_id, item.id)
    return _enrich_item_read(loaded_item)


async def discard_pantry_item(
    session: AsyncSession, user_id: UUID, item_id: UUID, discard_qty: Decimal
) -> PantryItemRead:
    """Discards/wastes quantity from item atomically."""
    item = await get_pantry_item(session, user_id, item_id)

    if discard_qty <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Discard quantity must be greater than zero.",
        )

    current_qty = Decimal(str(item.quantity))
    if discard_qty > current_qty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot discard {discard_qty} {item.unit}. Available stock is {current_qty} {item.unit}.",
        )

    item.quantity = current_qty - discard_qty
    if item.quantity == Decimal("0"):
        item.status = "discarded"

    log = PantryItemLog(
        pantry_item_id=item.id,
        action="DISCARDED",
        quantity_change=-discard_qty,
    )
    session.add(log)

    await session.commit()
    loaded_item = await get_pantry_item(session, user_id, item.id)
    return _enrich_item_read(loaded_item)


async def delete_pantry_item(session: AsyncSession, user_id: UUID, item_id: UUID) -> PantryItemRead:
    """Soft deletes pantry item."""
    item = await get_pantry_item(session, user_id, item_id)
    item.is_deleted = True
    await session.commit()
    return _enrich_item_read(item)


async def list_expiring_pantry_items(session: AsyncSession, user_id: UUID) -> List[PantryItemRead]:
    """Lists active consumer pantry items with valid expiry dates sorted by DTE ASC."""
    stmt = (
        select(PantryItem)
        .options(
            joinedload(PantryItem.product).joinedload(Product.category),
            joinedload(PantryItem.product).joinedload(Product.brand),
            joinedload(PantryItem.batch),
        )
        .join(ConsumerPantry)
        .where(
            ConsumerPantry.user_id == user_id,
            PantryItem.is_deleted == False,
            PantryItem.status == "active",
            PantryItem.expiry_date.isnot(None),
        )
        .order_by(PantryItem.expiry_date.asc())
    )

    res = await session.execute(stmt)
    items = res.scalars().unique().all()
    return [_enrich_item_read(item) for item in items]
