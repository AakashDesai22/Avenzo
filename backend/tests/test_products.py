"""
AVENZO Backend — Product Master, Publish Workflow & Marketplace Filtering Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_crud_flow(client: AsyncClient, admin_headers: dict, consumer_headers: dict):
    """Test product creation, duplicate SKU rejection, search, and deactivation."""
    # First create a category
    cat_res = await client.post("/api/v1/categories", json={"name": "Fresh Bakery"}, headers=admin_headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["id"]

    # Create Product
    product_payload = {
        "name": "Whole Wheat Bread 400g",
        "sku": "BAK-WWB-001",
        "barcode": "8901234567890",
        "category_id": cat_id,
        "unit_of_measure": "loaf",
        "unit_price": "45.00",
        "cost_price": "32.00",
        "shelf_life_days": 7,
        "has_expiry": True,
    }

    create_res = await client.post("/api/v1/products", json=product_payload, headers=admin_headers)
    assert create_res.status_code == 201
    prod_data = create_res.json()["data"]
    assert prod_data["sku"] == "BAK-WWB-001"
    assert prod_data["unit_price"] == "45.00"
    # New products default to unpublished (draft)
    assert prod_data["is_published"] is False
    prod_id = prod_data["id"]

    # Duplicate SKU should fail with 409
    dup_res = await client.post("/api/v1/products", json=product_payload, headers=admin_headers)
    assert dup_res.status_code == 409

    # Retrieve Product
    get_res = await client.get(f"/api/v1/products/{prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "Whole Wheat Bread 400g"

    # Search Products
    search_res = await client.get("/api/v1/products?search=Wheat")
    assert search_res.status_code == 200
    assert len(search_res.json()["data"]) >= 1

    # Consumer cannot create product (403)
    consumer_res = await client.post("/api/v1/products", json=product_payload, headers=consumer_headers)
    assert consumer_res.status_code == 403


@pytest.mark.asyncio
async def test_product_create_invalid_category(client: AsyncClient, admin_headers: dict):
    """Test product creation with non-existent category_id fails with 404."""
    invalid_payload = {
        "name": "Invalid Product",
        "sku": "INV-001",
        "category_id": "00000000-0000-0000-0000-000000000000",
        "unit_price": "10.00",
    }
    res = await client.post("/api/v1/products", json=invalid_payload, headers=admin_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_product_publish_unpublish_workflow(
    client: AsyncClient, admin_headers: dict, consumer_headers: dict
):
    """
    Full draft/publish workflow:
    1. Create product -> is_published=False (draft)
    2. Marketplace must NOT show it
    3. Publish -> is_published=True
    4. Marketplace MUST show it
    5. Unpublish -> is_published=False
    6. Marketplace must NOT show it again
    """
    # Create category
    cat_res = await client.post("/api/v1/categories", json={"name": "Dairy Draft Test"}, headers=admin_headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["id"]

    # Create product (draft by default)
    prod_res = await client.post(
        "/api/v1/products",
        json={
            "name": "Draft Milk 1L",
            "sku": "DRY-MLK-PUB-001",
            "category_id": cat_id,
            "unit_price": "25.00",
            "has_expiry": True,
            "shelf_life_days": 5,
        },
        headers=admin_headers,
    )
    assert prod_res.status_code == 201
    prod = prod_res.json()["data"]
    prod_id = prod["id"]
    assert prod["is_published"] is False

    # Consumer marketplace should NOT show this draft product
    mkt_res = await client.get("/api/v1/marketplace/products", headers=consumer_headers)
    assert mkt_res.status_code == 200
    marketplace_ids = [p["id"] for p in mkt_res.json()["data"]]
    assert prod_id not in marketplace_ids, "Draft product must not appear in marketplace"

    # Direct marketplace get should return 404 for draft
    mkt_detail = await client.get(f"/api/v1/marketplace/products/{prod_id}", headers=consumer_headers)
    assert mkt_detail.status_code == 404

    # Publish the product
    pub_res = await client.post(f"/api/v1/products/{prod_id}/publish", headers=admin_headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["data"]["is_published"] is True

    # Consumer marketplace MUST now show this product
    mkt_res2 = await client.get("/api/v1/marketplace/products", headers=consumer_headers)
    assert mkt_res2.status_code == 200
    marketplace_ids2 = [p["id"] for p in mkt_res2.json()["data"]]
    assert prod_id in marketplace_ids2, "Published product must appear in marketplace"

    # Direct marketplace get should now return 200
    mkt_detail2 = await client.get(f"/api/v1/marketplace/products/{prod_id}", headers=consumer_headers)
    assert mkt_detail2.status_code == 200

    # Unpublish the product
    unpub_res = await client.post(f"/api/v1/products/{prod_id}/unpublish", headers=admin_headers)
    assert unpub_res.status_code == 200
    assert unpub_res.json()["data"]["is_published"] is False

    # Consumer marketplace must NOT show it again
    mkt_res3 = await client.get("/api/v1/marketplace/products", headers=consumer_headers)
    assert mkt_res3.status_code == 200
    marketplace_ids3 = [p["id"] for p in mkt_res3.json()["data"]]
    assert prod_id not in marketplace_ids3, "Unpublished product must disappear from marketplace"


@pytest.mark.asyncio
async def test_publish_inactive_product_rejected(client: AsyncClient, admin_headers: dict):
    """Publishing a deactivated product must be rejected with 409."""
    # Create category
    cat_res = await client.post("/api/v1/categories", json={"name": "Inactive Pub Test"}, headers=admin_headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["id"]

    # Create + deactivate product
    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Inactive Item", "sku": "INACT-PUB-001", "category_id": cat_id, "unit_price": "10.00"},
        headers=admin_headers,
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["data"]["id"]

    # Deactivate
    del_res = await client.delete(f"/api/v1/products/{prod_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["is_active"] is False
    assert del_res.json()["data"]["is_published"] is False

    # Attempt to publish deactivated product should fail
    pub_res = await client.post(f"/api/v1/products/{prod_id}/publish", headers=admin_headers)
    assert pub_res.status_code == 409


@pytest.mark.asyncio
async def test_consumer_cannot_publish(client: AsyncClient, admin_headers: dict, consumer_headers: dict):
    """Consumer must not be able to call publish or unpublish endpoints."""
    cat_res = await client.post("/api/v1/categories", json={"name": "RBAC Pub Test"}, headers=admin_headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "RBAC Product", "sku": "RBAC-PUB-001", "category_id": cat_id, "unit_price": "10.00"},
        headers=admin_headers,
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["data"]["id"]

    pub_res = await client.post(f"/api/v1/products/{prod_id}/publish", headers=consumer_headers)
    assert pub_res.status_code == 403

    unpub_res = await client.post(f"/api/v1/products/{prod_id}/unpublish", headers=consumer_headers)
    assert unpub_res.status_code == 403


@pytest.mark.asyncio
async def test_list_products_is_published_filter(client: AsyncClient, admin_headers: dict):
    """The is_published query param must correctly filter draft vs published products."""
    cat_res = await client.post("/api/v1/categories", json={"name": "Filter Test Cat"}, headers=admin_headers)
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["data"]["id"]

    # Create two products
    draft_res = await client.post(
        "/api/v1/products",
        json={"name": "Draft Filter Item", "sku": "FILT-DRAFT-001", "category_id": cat_id, "unit_price": "5.00"},
        headers=admin_headers,
    )
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["data"]["id"]

    pub_res = await client.post(
        "/api/v1/products",
        json={"name": "Published Filter Item", "sku": "FILT-PUB-001", "category_id": cat_id, "unit_price": "5.00"},
        headers=admin_headers,
    )
    assert pub_res.status_code == 201
    pub_id = pub_res.json()["data"]["id"]

    # Publish only the second product
    await client.post(f"/api/v1/products/{pub_id}/publish", headers=admin_headers)

    # Filter published only
    pub_filter = await client.get(f"/api/v1/products?is_published=true&category_id={cat_id}")
    assert pub_filter.status_code == 200
    pub_ids = [p["id"] for p in pub_filter.json()["data"]]
    assert pub_id in pub_ids
    assert draft_id not in pub_ids

    # Filter drafts only
    draft_filter = await client.get(f"/api/v1/products?is_published=false&category_id={cat_id}")
    assert draft_filter.status_code == 200
    draft_ids = [p["id"] for p in draft_filter.json()["data"]]
    assert draft_id in draft_ids
    assert pub_id not in draft_ids


@pytest.mark.asyncio
async def test_publish_product_validations(client: AsyncClient, admin_headers: dict):
    """Publish endpoint validates active category and optional sellable stock requirement."""
    # 1. Product in inactive category cannot be published
    cat_res = await client.post(
        "/api/v1/categories", json={"name": "Inactive Pub Cat", "is_active": False}, headers=admin_headers
    )
    assert cat_res.status_code == 201
    inact_cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Valid Prod Inactive Cat", "sku": "PUB-VAL-001", "category_id": inact_cat_id, "unit_price": "10.00"},
        headers=admin_headers,
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["data"]["id"]

    pub_fail = await client.post(f"/api/v1/products/{prod_id}/publish", headers=admin_headers)
    assert pub_fail.status_code == 400
    assert "category" in pub_fail.json()["detail"].lower()

    # 2. require_stock=true fails when product has no inventory
    act_cat = await client.post("/api/v1/categories", json={"name": "Active Pub Cat"}, headers=admin_headers)
    act_cat_id = act_cat.json()["data"]["id"]

    no_stock_prod = await client.post(
        "/api/v1/products",
        json={"name": "Zero Stock Product", "sku": "PUB-VAL-002", "category_id": act_cat_id, "unit_price": "10.00"},
        headers=admin_headers,
    )
    no_stock_id = no_stock_prod.json()["data"]["id"]

    stock_fail = await client.post(
        f"/api/v1/products/{no_stock_id}/publish?require_stock=true", headers=admin_headers
    )
    assert stock_fail.status_code == 400
    assert "stock" in stock_fail.json()["detail"].lower()

