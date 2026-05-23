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
    client.post("/erp/orders", json={
        "order_no": "PO-2026-002",
        "product_spec": "110kV 套管",
        "quantity": 30,
    })
    # 查詢
    resp = client.get("/erp/orders/1")
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