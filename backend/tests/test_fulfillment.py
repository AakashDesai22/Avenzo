"""
AVENZO Backend — Phase 10C Order Fulfillment & FEFO Allocation Test Suite
Verifies order state machine transitions, server-side FEFO batch allocation,
multi-batch splits, physical stock deduction on dispatch, stock release on cancellation,
batch traceability chain, and RBAC authorization rules.
"""

import uuid
import pytest
from datetime import timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.date_utils import get_business_date
from app.models.product import Product, Category
from app.models.inventory import Inventory, Batch, InventoryTransaction
from app.models.warehouse import Warehouse
from app.models.order import Order, OrderItem
from app.models.order_allocation import OrderBatchAllocation


async def _create_test_order_helper(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, qty: int = 10
) -> tuple[dict, Product, Inventory, Batch]:
    """Helper to setup product, batch, inventory, and checkout order."""
    today = get_business_date()
    uid = uuid.uuid4().hex[:8]

    cat = Category(name=f"Fulfillment Test Category {uid}")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name=f"FEFO Test Milk {uid}",
        sku=f"FEFO-MILK-{uid}",
        category_id=cat.id,
        unit_price=Decimal("4.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name=f"Fulfillment Warehouse {uid}", city="Austin")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number=f"B-MILK-{uid}",
        expiry_date=today + timedelta(days=20),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=100,
        quantity_reserved=0,
    )
    db_session.add(inventory)
    await db_session.commit()

    # Clear active cart and checkout order
    await client.delete("/api/v1/cart", headers=consumer_headers)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": qty}, headers=consumer_headers
    )

    res = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "100 Fulfillment Way, Austin TX", "payment_method": "MOCK_PAYMENT"},
        headers=consumer_headers,
    )
    order_data = res.json()["data"]
    return order_data, product, inventory, batch


@pytest.mark.asyncio
async def test_confirm_order_success(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Business role can confirm a pending order."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=2)
    order_id = order_data["id"]

    res = await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_fefo_allocation_success_single_batch(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Business role can confirm and execute FEFO allocation for a single batch."""
    order_data, product, inventory, batch = await _create_test_order_helper(
        client, db_session, consumer_headers, qty=5
    )
    order_id = order_data["id"]

    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    alloc_res = await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)

    assert alloc_res.status_code == 200
    data = alloc_res.json()["data"]
    assert data["status"] == "ALLOCATED"
    assert data["items"][0]["fulfillment_status"] == "ALLOCATED"
    assert len(data["items"][0]["allocations"]) == 1

    alloc = data["items"][0]["allocations"][0]
    assert alloc["product_id"] == str(product.id)
    assert alloc["batch_id"] == str(batch.id)
    assert alloc["allocated_quantity"] == 5


@pytest.mark.asyncio
async def test_fefo_allocation_multi_batch_split(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """FEFO allocation splits an order item across multiple batches ordered by expiry ASC."""
    today = get_business_date()

    cat = Category(name="Multi Batch Cat")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Multi Batch Juice",
        sku="MB-JUICE-01",
        category_id=cat.id,
        unit_price=Decimal("6.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name="Juice Depot", city="Dallas")
    db_session.add_all([product, wh])
    await db_session.commit()

    # Earlier expiring batch (Expires in 10 days) -> 10 on hand
    batch_early = Batch(
        product_id=product.id,
        batch_number="B-EARLY-10",
        expiry_date=today + timedelta(days=10),
        status="active",
    )
    # Later expiring batch (Expires in 40 days) -> 20 on hand
    batch_late = Batch(
        product_id=product.id,
        batch_number="B-LATE-40",
        expiry_date=today + timedelta(days=40),
        status="active",
    )
    db_session.add_all([batch_early, batch_late])
    await db_session.commit()

    inv_early = Inventory(
        product_id=product.id, batch_id=batch_early.id, warehouse_id=wh.id, quantity_on_hand=10, quantity_reserved=0
    )
    inv_late = Inventory(
        product_id=product.id, batch_id=batch_late.id, warehouse_id=wh.id, quantity_on_hand=20, quantity_reserved=0
    )
    db_session.add_all([inv_early, inv_late])
    await db_session.commit()

    # Checkout order for 25 units -> Should take 10 from batch_early and 15 from batch_late
    await client.delete("/api/v1/cart", headers=consumer_headers)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 25}, headers=consumer_headers
    )
    chk_res = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "500 Juice Ave, Dallas TX", "payment_method": "MOCK_PAYMENT"},
        headers=consumer_headers,
    )
    order_id = chk_res.json()["data"]["id"]

    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    alloc_res = await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)

    assert alloc_res.status_code == 200
    allocations = alloc_res.json()["data"]["items"][0]["allocations"]
    assert len(allocations) == 2

    # Verify first allocation is from batch_early (10 units)
    assert allocations[0]["batch_id"] == str(batch_early.id)
    assert allocations[0]["allocated_quantity"] == 10

    # Verify second allocation is from batch_late (15 units)
    assert allocations[1]["batch_id"] == str(batch_late.id)
    assert allocations[1]["allocated_quantity"] == 15


@pytest.mark.asyncio
async def test_invalid_status_transition_rejected(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Attempting invalid state machine transitions returns 400 Bad Request."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=2)
    order_id = order_data["id"]

    # Try allocating PENDING order directly (must be CONFIRMED first)
    alloc_res = await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)
    assert alloc_res.status_code == 400
    assert "must be CONFIRMED" in alloc_res.json()["detail"]

    # Try dispatching PENDING order directly
    disp_res = await client.post(f"/api/v1/orders/{order_id}/dispatch", headers=manager_headers)
    assert disp_res.status_code == 400


@pytest.mark.asyncio
async def test_full_fulfillment_lifecycle_pack_ship_deliver(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Verifies complete fulfillment flow: PENDING -> CONFIRMED -> ALLOCATED -> PACKED -> SHIPPED -> DELIVERED."""
    order_data, product, inventory, _ = await _create_test_order_helper(
        client, db_session, consumer_headers, qty=4
    )
    order_id = order_data["id"]

    # 1. Confirm
    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    # 2. Allocate
    await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)
    # 3. Pack
    pack_res = await client.post(f"/api/v1/orders/{order_id}/pack", headers=manager_headers)
    assert pack_res.status_code == 200
    assert pack_res.json()["data"]["status"] == "PACKED"

    # 4. Dispatch (Deducts physical stock: quantity_on_hand -= 4, quantity_reserved -= 4)
    disp_res = await client.post(f"/api/v1/orders/{order_id}/dispatch", headers=manager_headers)
    assert disp_res.status_code == 200
    assert disp_res.json()["data"]["status"] == "SHIPPED"

    await db_session.refresh(inventory)
    assert inventory.quantity_on_hand == 96
    assert inventory.quantity_reserved == 0

    # Verify SALE audit transaction
    tx_res = await db_session.execute(
        select(InventoryTransaction).where(
            InventoryTransaction.inventory_id == inventory.id,
            InventoryTransaction.transaction_type == "SALE",
        )
    )
    tx = tx_res.scalars().first()
    assert tx is not None
    assert tx.quantity_change == -4

    # 5. Deliver
    del_res = await client.post(f"/api/v1/orders/{order_id}/deliver", headers=manager_headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["status"] == "DELIVERED"


@pytest.mark.asyncio
async def test_cancel_allocated_order_releases_stock(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Cancelling an ALLOCATED order releases quantity_reserved and deletes allocations."""
    order_data, _, inventory, _ = await _create_test_order_helper(
        client, db_session, consumer_headers, qty=6
    )
    order_id = order_data["id"]

    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)

    cancel_res = await client.post(f"/api/v1/orders/{order_id}/cancel", headers=manager_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"

    # Verify inventory reservation released (quantity_on_hand=100, quantity_reserved=0)
    await db_session.refresh(inventory)
    assert inventory.quantity_on_hand == 100
    assert inventory.quantity_reserved == 0

    # Verify RELEASE audit transaction
    tx_res = await db_session.execute(
        select(InventoryTransaction).where(
            InventoryTransaction.inventory_id == inventory.id,
            InventoryTransaction.transaction_type == "RELEASE",
        )
    )
    tx = tx_res.scalars().first()
    assert tx is not None
    assert tx.quantity_change == -6


@pytest.mark.asyncio
async def test_cancel_shipped_order_fails(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Attempting to cancel an order after dispatch (SHIPPED) returns 400 Bad Request."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=2)
    order_id = order_data["id"]

    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)
    await client.post(f"/api/v1/orders/{order_id}/pack", headers=manager_headers)
    await client.post(f"/api/v1/orders/{order_id}/dispatch", headers=manager_headers)

    res = await client.post(f"/api/v1/orders/{order_id}/cancel", headers=manager_headers)
    assert res.status_code == 400
    assert "dispatched" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_batch_traceability_endpoint(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Consumer and staff can query exact batch allocations for traceability."""
    order_data, product, _, batch = await _create_test_order_helper(
        client, db_session, consumer_headers, qty=3
    )
    order_id = order_data["id"]

    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)
    await client.post(f"/api/v1/orders/{order_id}/allocate", headers=manager_headers)

    res = await client.get(f"/api/v1/orders/{order_id}/allocations", headers=consumer_headers)
    assert res.status_code == 200
    allocs = res.json()["data"]
    assert len(allocs) == 1
    assert allocs[0]["product_id"] == str(product.id)
    assert allocs[0]["batch_id"] == str(batch.id)
    assert allocs[0]["batch_number"] == batch.batch_number
    assert allocs[0]["allocated_quantity"] == 3


@pytest.mark.asyncio
async def test_consumer_cannot_trigger_fulfillment_mutations(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Consumer role is denied access to operational fulfillment mutations (403 Forbidden)."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=1)
    order_id = order_data["id"]

    res_confirm = await client.post(f"/api/v1/orders/{order_id}/confirm", headers=consumer_headers)
    assert res_confirm.status_code == 403

    res_allocate = await client.post(f"/api/v1/orders/{order_id}/allocate", headers=consumer_headers)
    assert res_allocate.status_code == 403


@pytest.mark.asyncio
async def test_staff_cannot_trigger_fulfillment_mutations(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, staff_headers: dict
):
    """STAFF role is read-only and cannot trigger fulfillment mutations (403 Forbidden)."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=1)
    order_id = order_data["id"]

    res_confirm = await client.post(f"/api/v1/orders/{order_id}/confirm", headers=staff_headers)
    assert res_confirm.status_code == 403

    res_pack = await client.post(f"/api/v1/orders/{order_id}/pack", headers=staff_headers)
    assert res_pack.status_code == 403

    # But STAFF CAN read allocations
    res_alloc = await client.get(f"/api/v1/orders/{order_id}/allocations", headers=staff_headers)
    assert res_alloc.status_code == 200


@pytest.mark.asyncio
async def test_business_list_all_orders_admin_manager_staff(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict, staff_headers: dict
):
    """ADMIN, BUSINESS_MANAGER, and STAFF can query the business order queue, but CONSUMER cannot."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=2)
    order_id = order_data["id"]

    # Manager can list orders
    res_mgr = await client.get("/api/v1/orders", headers=manager_headers)
    assert res_mgr.status_code == 200
    assert len(res_mgr.json()["data"]) >= 1

    # Staff can list orders
    res_staff = await client.get("/api/v1/orders", headers=staff_headers)
    assert res_staff.status_code == 200
    assert len(res_staff.json()["data"]) >= 1

    # Consumer cannot use business order list (403 Forbidden)
    res_cons = await client.get("/api/v1/orders", headers=consumer_headers)
    assert res_cons.status_code == 403


@pytest.mark.asyncio
async def test_business_list_orders_status_filter(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, manager_headers: dict
):
    """Business order list supports status filtering."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=2)
    order_id = order_data["id"]

    # Pending filter
    res_pending = await client.get("/api/v1/orders?status=PENDING", headers=manager_headers)
    assert res_pending.status_code == 200
    assert any(o["id"] == order_id for o in res_pending.json()["data"])

    # Confirm order
    await client.post(f"/api/v1/orders/{order_id}/confirm", headers=manager_headers)

    # Pending filter no longer contains order
    res_pending_after = await client.get("/api/v1/orders?status=PENDING", headers=manager_headers)
    assert not any(o["id"] == order_id for o in res_pending_after.json()["data"])

    # Confirmed filter contains order
    res_confirmed = await client.get("/api/v1/orders?status=CONFIRMED", headers=manager_headers)
    assert res_confirmed.status_code == 200
    assert any(o["id"] == order_id for o in res_confirmed.json()["data"])


@pytest.mark.asyncio
async def test_business_get_order_by_id(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict, staff_headers: dict
):
    """Business roles can get detailed order view by ID."""
    order_data, _, _, _ = await _create_test_order_helper(client, db_session, consumer_headers, qty=2)
    order_id = order_data["id"]

    res = await client.get(f"/api/v1/orders/{order_id}", headers=staff_headers)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == order_id
    assert res.json()["data"]["status"] == "PENDING"
