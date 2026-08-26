"""
AVENZO Backend — Phase 10A Consumer Marketplace API Test Suite
Verifies consumer marketplace endpoints, sellable stock aggregation,
expiry filtering, reservation deductions, search/category filters, security, and leak-prevention.
"""

import pytest
from datetime import timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.date_utils import get_business_date
from app.models.product import Product, Category
from app.models.inventory import Inventory, Batch
from app.models.warehouse import Warehouse
from app.models.supplier import Supplier


@pytest.mark.asyncio
async def test_marketplace_consumer_auth_required(client: AsyncClient):
    """Unauthenticated requests to marketplace endpoints should return 401/403."""
    response = await client.get("/api/v1/marketplace/products")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_marketplace_list_products_success(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Product with available stock appears in consumer marketplace list."""
    today = get_business_date()

    category = Category(name="Marketplace Dairy")
    db_session.add(category)
    await db_session.commit()

    product = Product(
        name="Fresh Whole Milk 1L",
        sku="MK-MKT-001",
        category_id=category.id,
        unit_price=Decimal("3.99"),
        cost_price=Decimal("2.10"),
        reorder_point=10,
        has_expiry=True,
        is_active=True,
    )
    supplier = Supplier(name="Local Dairy Farm")
    warehouse = Warehouse(name="Central Market Hub", city="Austin")
    db_session.add_all([product, supplier, warehouse])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="B-MILK-101",
        expiry_date=today + timedelta(days=15),
        supplier_id=supplier.id,
        initial_quantity=100,
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=warehouse.id,
        quantity_on_hand=50,
        quantity_reserved=0,
    )
    db_session.add(inventory)
    await db_session.commit()

    response = await client.get("/api/v1/marketplace/products", headers=consumer_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True

    items = res_data["data"]
    matched = [item for item in items if item["id"] == str(product.id)]
    assert len(matched) == 1
    p_item = matched[0]
    assert p_item["name"] == "Fresh Whole Milk 1L"
    assert p_item["unit_price"] == "3.99"
    assert p_item["available_quantity"] == 50
    assert p_item["is_available"] is True

    # Security check: Internal fields MUST NOT be leaked
    assert "cost_price" not in p_item
    assert "reorder_point" not in p_item
    assert "quantity_on_hand" not in p_item
    assert "quantity_reserved" not in p_item
    assert "warehouse_id" not in p_item


@pytest.mark.asyncio
async def test_marketplace_reserved_quantity_deduction(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Reserved stock (quantity_reserved) reduces sellable availability (on_hand - reserved)."""
    today = get_business_date()

    category = Category(name="Marketplace Produce")
    db_session.add(category)
    await db_session.commit()

    product = Product(
        name="Organic Honey Crisp Apples",
        sku="AP-MKT-002",
        category_id=category.id,
        unit_price=Decimal("4.50"),
        has_expiry=True,
        is_active=True,
    )
    warehouse = Warehouse(name="Produce Depot", city="Dallas")
    db_session.add_all([product, warehouse])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="B-APPLE-201",
        expiry_date=today + timedelta(days=10),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    # 40 on hand, 15 reserved -> 25 available
    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=warehouse.id,
        quantity_on_hand=40,
        quantity_reserved=15,
    )
    db_session.add(inventory)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/marketplace/products/{product.id}", headers=consumer_headers
    )
    assert response.status_code == 200
    p_item = response.json()["data"]
    assert p_item["available_quantity"] == 25
    assert p_item["is_available"] is True


@pytest.mark.asyncio
async def test_marketplace_expired_batch_excluded(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Expired batch stock (expiry_date < business_date) is excluded from sellable quantity."""
    today = get_business_date()

    category = Category(name="Marketplace Bakery")
    db_session.add(category)
    await db_session.commit()

    product = Product(
        name="Artisan Sourdough Loaf",
        sku="BK-MKT-003",
        category_id=category.id,
        unit_price=Decimal("5.99"),
        has_expiry=True,
        is_active=True,
    )
    warehouse = Warehouse(name="Bakery Hub", city="Houston")
    db_session.add_all([product, warehouse])
    await db_session.commit()

    # Expired batch
    expired_batch = Batch(
        product_id=product.id,
        batch_number="B-BREAD-OLD",
        expiry_date=today - timedelta(days=2),
        status="active",
    )
    db_session.add(expired_batch)
    await db_session.commit()

    inventory = Inventory(
        product_id=product.id,
        batch_id=expired_batch.id,
        warehouse_id=warehouse.id,
        quantity_on_hand=30,
        quantity_reserved=0,
    )
    db_session.add(inventory)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/marketplace/products/{product.id}", headers=consumer_headers
    )
    assert response.status_code == 200
    p_item = response.json()["data"]
    assert p_item["available_quantity"] == 0
    assert p_item["is_available"] is False


@pytest.mark.asyncio
async def test_marketplace_multiple_batches_aggregate(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Multiple active non-expired batches for the same product aggregate sellable quantities."""
    today = get_business_date()

    category = Category(name="Marketplace Beverages")
    db_session.add(category)
    await db_session.commit()

    product = Product(
        name="Cold Pressed Orange Juice 500ml",
        sku="BV-MKT-004",
        category_id=category.id,
        unit_price=Decimal("2.99"),
        has_expiry=True,
        is_active=True,
    )
    warehouse = Warehouse(name="Beverage Cold Storage", city="Seattle")
    db_session.add_all([product, warehouse])
    await db_session.commit()

    batch_1 = Batch(
        product_id=product.id,
        batch_number="B-JUICE-01",
        expiry_date=today + timedelta(days=5),
        status="active",
    )
    batch_2 = Batch(
        product_id=product.id,
        batch_number="B-JUICE-02",
        expiry_date=today + timedelta(days=20),
        status="active",
    )
    db_session.add_all([batch_1, batch_2])
    await db_session.commit()

    inv_1 = Inventory(
        product_id=product.id,
        batch_id=batch_1.id,
        warehouse_id=warehouse.id,
        quantity_on_hand=20,
        quantity_reserved=5, # 15 available
    )
    inv_2 = Inventory(
        product_id=product.id,
        batch_id=batch_2.id,
        warehouse_id=warehouse.id,
        quantity_on_hand=35,
        quantity_reserved=0, # 35 available
    )
    db_session.add_all([inv_1, inv_2])
    await db_session.commit()

    response = await client.get(
        f"/api/v1/marketplace/products/{product.id}", headers=consumer_headers
    )
    assert response.status_code == 200
    p_item = response.json()["data"]
    assert p_item["available_quantity"] == 50 # 15 + 35
    assert p_item["is_available"] is True


@pytest.mark.asyncio
async def test_marketplace_inactive_or_deleted_product_excluded(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Inactive or deleted products are excluded from marketplace listing and return 404 on detail."""
    category = Category(name="Marketplace Snacks")
    db_session.add(category)
    await db_session.commit()

    inactive_product = Product(
        name="Discontinued Chips",
        sku="SN-MKT-OFF",
        category_id=category.id,
        unit_price=Decimal("1.99"),
        is_active=False,
    )
    db_session.add(inactive_product)
    await db_session.commit()

    list_res = await client.get("/api/v1/marketplace/products", headers=consumer_headers)
    assert list_res.status_code == 200
    matched = [p for p in list_res.json()["data"] if p["id"] == str(inactive_product.id)]
    assert len(matched) == 0

    detail_res = await client.get(
        f"/api/v1/marketplace/products/{inactive_product.id}", headers=consumer_headers
    )
    assert detail_res.status_code == 404


@pytest.mark.asyncio
async def test_marketplace_detail_not_found(client: AsyncClient, consumer_headers: dict):
    """Non-existent product ID returns 404 Not Found."""
    fake_uuid = "00000000-0000-0000-0000-000000009999"
    response = await client.get(f"/api/v1/marketplace/products/{fake_uuid}", headers=consumer_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_marketplace_search_and_category_filter(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Search query and category filtering work correctly on marketplace list."""
    cat_a = Category(name="Cat Premium Organic")
    cat_b = Category(name="Cat Standard Pantry")
    db_session.add_all([cat_a, cat_b])
    await db_session.commit()

    prod_1 = Product(
        name="Matcha Green Tea Powder",
        sku="TEA-MKT-01",
        category_id=cat_a.id,
        unit_price=Decimal("19.99"),
        is_active=True,
    )
    prod_2 = Product(
        name="Black Earl Grey Tea",
        sku="TEA-MKT-02",
        category_id=cat_b.id,
        unit_price=Decimal("8.99"),
        is_active=True,
    )
    db_session.add_all([prod_1, prod_2])
    await db_session.commit()

    # Search filter
    res_search = await client.get(
        "/api/v1/marketplace/products?search=Matcha", headers=consumer_headers
    )
    assert res_search.status_code == 200
    search_data = res_search.json()["data"]
    assert any(p["id"] == str(prod_1.id) for p in search_data)
    assert not any(p["id"] == str(prod_2.id) for p in search_data)

    # Category filter
    res_cat = await client.get(
        f"/api/v1/marketplace/products?category_id={cat_b.id}", headers=consumer_headers
    )
    assert res_cat.status_code == 200
    cat_data = res_cat.json()["data"]
    assert any(p["id"] == str(prod_2.id) for p in cat_data)
    assert not any(p["id"] == str(prod_1.id) for p in cat_data)
