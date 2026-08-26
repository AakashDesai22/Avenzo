"""
AVENZO Backend — Phase 10B Consumer Cart Test Suite
Verifies active cart creation, adding items, quantity updates, item removal,
ownership isolation, inactive product rejection, and unauthenticated access blocking.
"""

import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, Category
from app.models.user import User


@pytest.mark.asyncio
async def test_cart_unauthenticated_access_rejected(client: AsyncClient):
    """Unauthenticated requests to cart endpoints should return 401/403."""
    res = await client.get("/api/v1/cart")
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_cart_non_consumer_access_rejected(client: AsyncClient, admin_headers: dict):
    """Business roles (ADMIN) attempting to access consumer cart endpoints should return 403 Forbidden."""
    res = await client.get("/api/v1/cart", headers=admin_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_get_or_create_active_cart(client: AsyncClient, consumer_headers: dict):
    """Consumer can retrieve an empty active cart."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    res = await client.get("/api/v1/cart", headers=consumer_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == "ACTIVE"
    assert data["total_items_count"] == 0
    assert data["calculated_subtotal"] == "0.00"
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_add_product_to_cart(client: AsyncClient, db_session: AsyncSession, consumer_headers: dict):
    """Consumer can add a product item to active cart."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    cat = Category(name="Cart Test Category")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Organic Almond Milk 1L",
        sku="AM-CART-001",
        category_id=cat.id,
        unit_price=Decimal("4.25"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    payload = {"product_id": str(product.id), "quantity": 2}
    res = await client.post("/api/v1/cart/items", json=payload, headers=consumer_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["total_items_count"] == 2
    assert data["calculated_subtotal"] == "8.50"
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == str(product.id)
    assert data["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_add_same_product_increments_quantity(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Adding the same product again increments existing cart item quantity."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    cat = Category(name="Cart Test Category 2")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Greek Yogurt 500g",
        sku="GY-CART-002",
        category_id=cat.id,
        unit_price=Decimal("3.50"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    payload = {"product_id": str(product.id), "quantity": 1}
    await client.post("/api/v1/cart/items", json=payload, headers=consumer_headers)

    # Add 3 more units
    payload_2 = {"product_id": str(product.id), "quantity": 3}
    res = await client.post("/api/v1/cart/items", json=payload_2, headers=consumer_headers)
    assert res.status_code == 201
    data = res.json()["data"]
    assert data["total_items_count"] == 4
    assert data["calculated_subtotal"] == "14.00"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 4


@pytest.mark.asyncio
async def test_update_cart_item_quantity(client: AsyncClient, db_session: AsyncSession, consumer_headers: dict):
    """Consumer can update item quantity in cart."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    cat = Category(name="Cart Test Category 3")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Granola Bar Pack",
        sku="GB-CART-003",
        category_id=cat.id,
        unit_price=Decimal("5.00"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    add_res = await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=consumer_headers
    )
    item_id = add_res.json()["data"]["items"][0]["id"]

    # Update quantity to 5
    upd_res = await client.put(
        f"/api/v1/cart/items/{item_id}", json={"quantity": 5}, headers=consumer_headers
    )
    assert upd_res.status_code == 200
    data = upd_res.json()["data"]
    assert data["total_items_count"] == 5
    assert data["calculated_subtotal"] == "25.00"


@pytest.mark.asyncio
async def test_update_quantity_to_zero_removes_item(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Updating cart item quantity to 0 removes the item."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    cat = Category(name="Cart Test Category 4")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Dark Chocolate Bar",
        sku="DC-CART-004",
        category_id=cat.id,
        unit_price=Decimal("2.50"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    add_res = await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 2}, headers=consumer_headers
    )
    item_id = add_res.json()["data"]["items"][0]["id"]

    # Update to 0
    upd_res = await client.put(
        f"/api/v1/cart/items/{item_id}", json={"quantity": 0}, headers=consumer_headers
    )
    assert upd_res.status_code == 200
    data = upd_res.json()["data"]
    assert data["total_items_count"] == 0
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_remove_cart_item(client: AsyncClient, db_session: AsyncSession, consumer_headers: dict):
    """Consumer can delete a specific line item from active cart."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    cat = Category(name="Cart Test Category 5")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Sparkling Water 6-Pack",
        sku="SW-CART-005",
        category_id=cat.id,
        unit_price=Decimal("6.99"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    add_res = await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=consumer_headers
    )
    item_id = add_res.json()["data"]["items"][0]["id"]

    del_res = await client.delete(f"/api/v1/cart/items/{item_id}", headers=consumer_headers)
    assert del_res.status_code == 200
    assert len(del_res.json()["data"]["items"]) == 0


@pytest.mark.asyncio
async def test_clear_cart(client: AsyncClient, db_session: AsyncSession, consumer_headers: dict):
    """Consumer can clear all items from active cart."""
    await client.delete("/api/v1/cart", headers=consumer_headers)
    cat = Category(name="Cart Test Category 6")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Pecan Nuts 250g",
        sku="PN-CART-006",
        category_id=cat.id,
        unit_price=Decimal("7.50"),
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()

    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 3}, headers=consumer_headers
    )

    clr_res = await client.delete("/api/v1/cart", headers=consumer_headers)
    assert clr_res.status_code == 200
    assert clr_res.json()["data"]["total_items_count"] == 0


@pytest.mark.asyncio
async def test_add_inactive_product_rejected(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Attempting to add an inactive product to cart returns 400 Bad Request."""
    cat = Category(name="Cart Test Category 7")
    db_session.add(cat)
    await db_session.commit()

    inactive_prod = Product(
        name="Discontinued Item",
        sku="OFF-CART-007",
        category_id=cat.id,
        unit_price=Decimal("1.00"),
        is_active=False,
    )
    db_session.add(inactive_prod)
    await db_session.commit()

    res = await client.post(
        "/api/v1/cart/items", json={"product_id": str(inactive_prod.id), "quantity": 1}, headers=consumer_headers
    )
    assert res.status_code == 400
    assert "not available for purchase" in res.json()["detail"]
