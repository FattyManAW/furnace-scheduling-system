"""Integration tests for erp_sim module"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Ensure ERP models are registered before table creation happens in conftest
import erp_sim.models  # noqa: E402, F401


def test_create_order_200(client):
    """建立訂單應回傳 200"""
    resp = client.post("/erp/orders", json={
        "order_no": "PO-2026-001",
        "product_spec": "220kV 套管",
        "quantity": 50,
        "priority": "high",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["order_no"] == "PO-2026-001"
    assert data["status"] == "pending"
    assert data["quantity"] == 50


def test_get_order_200(client):
    """查詢訂單應回傳 200"""
    # 先建立
    create_resp = client.post("/erp/orders", json={
        "order_no": "PO-2026-002",
        "product_spec": "110kV 套管",
        "quantity": 30,
    })
    order_id = create_resp.json()["id"]
    # 查詢
    resp = client.get(f"/erp/orders/{order_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["order_no"] == "PO-2026-002"


def test_list_orders_200(client):
    """列出訂單應回傳 200"""
    client.post("/erp/orders", json={
        "order_no": "PO-2026-003", "product_spec": "66kV 套管", "quantity": 20,
    })
    resp = client.get("/erp/orders")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_delivery_200(client):
    """建立交期應回傳 200"""
    client.post("/erp/orders", json={
        "order_no": "PO-2026-004",
        "product_spec": "220kV 套管",
        "quantity": 100,
    })
    resp = client.post("/erp/orders/1/delivery", json={
        "scheduled_date": "2026-06-15",
        "delivery_date": "2026-06-20",
        "furnace_id": "kiln-1",
        "est_hours": 80.0,
        "quantity": 100,
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["order_id"] == 1
    assert data["delivery_date"] == "2026-06-20"
    assert data["furnace_id"] == "kiln-1"


def test_delivery_date_is_realistic(client):
    """交期日期應是真實日期（非 2099 年）"""
    client.post("/erp/orders", json={
        "order_no": "PO-2026-005",
        "product_spec": "220kV 套管",
        "quantity": 80,
    })
    resp = client.post("/erp/orders/1/delivery", json={
        "scheduled_date": "2026-06-01",
        "delivery_date": "2026-06-10",
        "furnace_id": "kiln-2",
        "est_hours": 160.0,
        "quantity": 80,
    })
    assert resp.status_code == 200
    data = resp.json()
    delivery_date = data["delivery_date"]

    # Parse year — must be reasonable (not 2099)
    import datetime
    year = int(delivery_date.split("-")[0])
    current_year = datetime.date.today().year
    assert 2024 <= year <= current_year + 2, f"交期年份不合理: {delivery_date}"


def test_list_deliveries_200(client):
    """列出交期應回傳 200"""
    client.post("/erp/orders", json={
        "order_no": "PO-2026-006", "product_spec": "110kV 套管", "quantity": 60,
    })
    client.post("/erp/orders/1/delivery", json={
        "scheduled_date": "2026-07-01",
        "delivery_date": "2026-07-08",
        "furnace_id": "kiln-3",
        "est_hours": 120.0,
        "quantity": 60,
    })
    resp = client.get("/erp/deliveries")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_production_status_200(client):
    """生產狀態摘要應回傳 200"""
    client.post("/erp/orders", json={
        "order_no": "PO-2026-007", "product_spec": "220kV 套管", "quantity": 40,
    })
    resp = client.get("/erp/production-status")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "orders" in data
    assert "deliveries" in data
    assert "total_quantity" in data


def test_sync_schedule(client):
    """同步排程結果到 ERP 應回傳 200"""
    client.post("/erp/orders", json={
        "order_no": "TEST-001",
        "product_spec": "220kV 套管",
        "quantity": 100,
    })
    schedule_result = {
        "order_schedule": [
            {
                "plan_no": "TEST-001",
                "contract_no": "C-001",
                "voltage_kv": 220.0,
                "qty": 100,
                "delivery_date": "2026-06-01",
                "kiln_id": "kiln-1",
                "kiln_name": "干燥罐 #1",
                "mold_od": 120.0,
                "mold_len": 200.0,
                "est_hours": 80.0,
                "status": "scheduled",
            }
        ]
    }
    resp = client.post("/erp/sync-schedule", json={"schedule_result": schedule_result})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["synced"] == 1
    assert data["errors"] == 0

    # 驗證 delivery_date 是合理日期
    deliveries_resp = client.get("/erp/deliveries")
    assert deliveries_resp.status_code == 200
    deliveries = deliveries_resp.json()
    assert len(deliveries) >= 1
    delivery_date = deliveries[0]["delivery_date"]
    year = int(delivery_date.split("-")[0])
    import datetime
    current_year = datetime.date.today().year
    assert 2024 <= year <= current_year + 2, f"同步後的交期年份不合理: {delivery_date}"


def test_duplicate_order_400(client):
    """重複建立相同訂單應回傳 400"""
    client.post("/erp/orders", json={
        "order_no": "PO-DUP-001", "product_spec": "test", "quantity": 10,
    })
    resp = client.post("/erp/orders", json={
        "order_no": "PO-DUP-001", "product_spec": "test", "quantity": 10,
    })
    assert resp.status_code == 400, resp.text
    assert "已存在" in resp.json()["detail"]


def test_order_not_found_404(client):
    """查詢不存在的訂單應回傳 404"""
    resp = client.get("/erp/orders/99999")
    assert resp.status_code == 404


# ── Repository unit tests (direct, not via HTTP) ────────────────────────

def test_list_orders_with_status_filter(db_session):
    """list_orders with status filter 應正確過濾"""
    from erp_sim.repository import create_order, list_orders, update_order_status

    o1 = create_order(db_session, "PO-SF-001", "spec A", 10, "normal")
    o2 = create_order(db_session, "PO-SF-002", "spec B", 20, "high")
    o3 = create_order(db_session, "PO-SF-003", "spec C", 30, "normal")
    update_order_status(db_session, o1.id, "scheduled")

    pending = list_orders(db_session, status="pending")
    assert len(pending) >= 2
    assert all(o.status == "pending" for o in pending)
    assert any(o.order_no == "PO-SF-002" for o in pending)

    scheduled = list_orders(db_session, status="scheduled")
    assert len(scheduled) >= 1
    assert any(o.order_no == "PO-SF-001" and o.status == "scheduled" for o in scheduled)


def test_get_deliveries_by_order(db_session):
    """get_deliveries_by_order 應回傳指定訂單的全部交期"""
    from erp_sim.repository import create_delivery, create_order, get_deliveries_by_order

    o1 = create_order(db_session, "PO-GDBO-001", "spec A", 10)
    o2 = create_order(db_session, "PO-GDBO-002", "spec B", 20)
    create_delivery(db_session, order_id=o1.id, order_no="PO-GDBO-001", furnace_id="k1")
    create_delivery(db_session, order_id=o1.id, order_no="PO-GDBO-001", furnace_id="k2")
    create_delivery(db_session, order_id=o2.id, order_no="PO-GDBO-002", furnace_id="k3")

    results = get_deliveries_by_order(db_session, o1.id)
    assert len(results) == 2
    assert all(d.order_id == o1.id for d in results)

    results2 = get_deliveries_by_order(db_session, o2.id)
    assert len(results2) == 1
    assert results2[0].order_id == o2.id

    results3 = get_deliveries_by_order(db_session, 99999)
    assert results3 == []


def test_list_deliveries_no_filter(db_session):
    """list_deliveries without any filter 應回傳全部"""
    from erp_sim.repository import create_delivery, create_order, list_deliveries

    o = create_order(db_session, "PO-LD-NF-001", "spec A", 10)
    create_delivery(db_session, order_id=o.id, order_no="PO-LD-NF-001", furnace_id="k1")
    create_delivery(db_session, order_id=o.id, order_no="PO-LD-NF-001", furnace_id="k2")

    results = list_deliveries(db_session)
    assert len(results) >= 2
    our_deliveries = [d for d in results if d.order_no == "PO-LD-NF-001"]
    assert len(our_deliveries) == 2


def test_list_deliveries_with_order_id_filter(db_session):
    """list_deliveries with order_id filter 應正確過濾"""
    from erp_sim.repository import create_delivery, create_order, list_deliveries

    o1 = create_order(db_session, "PO-LD-OIF-001", "spec A", 10)
    o2 = create_order(db_session, "PO-LD-OIF-002", "spec B", 20)
    create_delivery(db_session, order_id=o1.id, order_no="PO-LD-OIF-001", furnace_id="k1")
    create_delivery(db_session, order_id=o2.id, order_no="PO-LD-OIF-002", furnace_id="k2")

    results = list_deliveries(db_session, order_id=o1.id)
    assert len(results) == 1
    assert results[0].order_id == o1.id
    assert results[0].order_no == "PO-LD-OIF-001"


def test_list_deliveries_with_status_filter(db_session):
    """list_deliveries with status filter 應正確過濾"""
    from erp_sim.repository import create_delivery, create_order, list_deliveries
    from erp_sim.repository import update_delivery_status

    o = create_order(db_session, "PO-LDS-001", "spec A", 10)
    create_delivery(db_session, order_id=o.id, order_no="PO-LDS-001", status="scheduled")
    create_delivery(db_session, order_id=o.id, order_no="PO-LDS-001", status="delivered")

    scheduled = list_deliveries(db_session, status="scheduled")
    assert len(scheduled) >= 1
    assert any(d.status == "scheduled" and d.order_no == "PO-LDS-001" for d in scheduled)

    delivered = list_deliveries(db_session, status="delivered")
    assert len(delivered) >= 1
    assert any(d.status == "delivered" and d.order_no == "PO-LDS-001" for d in delivered)


def test_update_delivery_status_happy_path(db_session):
    """update_delivery_status 應正確更新交期狀態"""
    from erp_sim.repository import create_delivery, create_order, update_delivery_status, list_deliveries

    o = create_order(db_session, "PO-UDS-001", "spec A", 10)
    d = create_delivery(db_session, order_id=o.id, order_no="PO-UDS-001", status="scheduled")

    updated = update_delivery_status(db_session, delivery_id=d.id, status="in_progress")
    assert updated is not None
    assert updated.status == "in_progress"

    # 確認持久化
    results = list_deliveries(db_session)
    our_delivery = next((r for r in results if r.id == d.id), None)
    assert our_delivery is not None
    assert our_delivery.status == "in_progress"


# ── Sync unit tests ─────────────────────────────────────────────────────

def test_parse_date_invalid_fallback():
    """_compute_delivery_date with invalid date string → fallback to today"""
    from erp_sim.sync import _compute_delivery_date
    from datetime import date

    result = _compute_delivery_date("not-a-date", 8.0)
    today = date.today().strftime("%Y-%m-%d")
    # 應該回傳未來日期（非 today），因為 est_hours > 0 會加工作日
    assert "2099" not in result
    assert result >= today


def test_parse_date_zero_est_hours():
    """_compute_delivery_date with est_hours=0 → return base date unchanged"""
    from erp_sim.sync import _compute_delivery_date

    result = _compute_delivery_date("2026-06-01", 0.0)
    assert result == "2026-06-01"

    result2 = _compute_delivery_date("2026-06-01", -5.0)
    assert result2 == "2026-06-01"


def test_sync_schedule_skipped_no_plan_no(db_session):
    """sync with entry missing plan_no → skipped += 1"""
    from erp_sim.sync import sync_schedule_to_erp

    schedule_result = {
        "order_schedule": [
            {"plan_no": "", "delivery_date": "2026-06-01", "est_hours": 8.0},
        ]
    }
    result = sync_schedule_to_erp(db_session, schedule_result)
    assert result["skipped"] == 1
    assert result["synced"] == 0
    assert result["errors"] == 0


def test_sync_schedule_skipped_no_matching_order(db_session):
    """sync with plan_no that has no matching ERP order → skipped += 1"""
    from erp_sim.sync import sync_schedule_to_erp

    schedule_result = {
        "order_schedule": [
            {"plan_no": "NONEXISTENT", "delivery_date": "2026-06-01", "est_hours": 8.0},
        ]
    }
    result = sync_schedule_to_erp(db_session, schedule_result)
    assert result["skipped"] == 1
    assert result["synced"] == 0
    assert result["errors"] == 0


def test_sync_schedule_exception_error(db_session, monkeypatch):
    """sync with create_delivery raising exception → errors += 1"""
    from erp_sim.repository import create_order
    from erp_sim.sync import sync_schedule_to_erp

    create_order(db_session, "PO-ERR-001", "spec A", 10)

    # Mock create_delivery to raise
    import erp_sim.sync as sync_mod

    def mock_create_delivery(**kwargs):
        raise RuntimeError("simulated db error")

    monkeypatch.setattr(sync_mod, "create_delivery", mock_create_delivery)

    schedule_result = {
        "order_schedule": [
            {"plan_no": "PO-ERR-001", "delivery_date": "2026-06-01", "est_hours": 8.0},
        ]
    }
    result = sync_schedule_to_erp(db_session, schedule_result)
    assert result["errors"] == 1
    assert result["synced"] == 0
    assert result["skipped"] == 0