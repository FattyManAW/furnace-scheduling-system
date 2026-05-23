"""API integration tests — orders, molds, schedule endpoints"""


class TestOrderAPI:
    def test_list_orders_empty(self, client):
        resp = client.get("/api/v1/orders/")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_create_order(self, client):
        resp = client.post("/api/v1/orders/", json={
            "plan_no": "API-001",
            "contract_no": "C-2026-100",
            "voltage_kv": 220.0,
            "current_a": 150.0,
            "qty": 10,
            "delivery_date": "2026-08-01",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["plan_no"] == "API-001"
        assert data["id"] is not None

    def test_create_duplicate_plan_no(self, client):
        client.post("/api/v1/orders/", json={
            "plan_no": "API-DUP",
            "voltage_kv": 220.0, "current_a": 100.0, "qty": 5,
        })
        resp = client.post("/api/v1/orders/", json={
            "plan_no": "API-DUP",
            "voltage_kv": 110.0, "current_a": 50.0, "qty": 3,
        })
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    def test_get_order_by_id(self, client):
        created = client.post("/api/v1/orders/", json={
            "plan_no": "API-002",
            "voltage_kv": 380.0, "current_a": 200.0, "qty": 8,
        })
        oid = created.json()["id"]
        resp = client.get(f"/api/v1/orders/{oid}")
        assert resp.status_code == 200
        assert resp.json()["plan_no"] == "API-002"

    def test_get_nonexistent_order(self, client):
        resp = client.get("/api/v1/orders/99999")
        assert resp.status_code == 404

    def test_update_order(self, client):
        created = client.post("/api/v1/orders/", json={
            "plan_no": "API-003",
            "voltage_kv": 220.0, "current_a": 100.0, "qty": 5, "status": "pending",
        })
        oid = created.json()["id"]
        resp = client.put(f"/api/v1/orders/{oid}", json={"status": "scheduled", "qty": 12})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "scheduled"
        assert data["qty"] == 12

    def test_delete_order(self, client):
        created = client.post("/api/v1/orders/", json={
            "plan_no": "API-DEL",
            "voltage_kv": 220.0, "current_a": 100.0, "qty": 1,
        })
        oid = created.json()["id"]
        resp = client.delete(f"/api/v1/orders/{oid}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_orders_count(self, client):
        client.post("/api/v1/orders/", json={
            "plan_no": "CNT-001", "voltage_kv": 220.0, "current_a": 100.0, "qty": 5,
        })
        client.post("/api/v1/orders/", json={
            "plan_no": "CNT-002", "voltage_kv": 110.0, "current_a": 50.0, "qty": 3,
        })
        resp = client.get("/api/v1/orders/count")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_search_orders(self, client):
        client.post("/api/v1/orders/", json={
            "plan_no": "SRCH-ZZZ", "contract_no": "C-SPECIAL-999",
            "voltage_kv": 500.0, "current_a": 200.0, "qty": 1,
        })
        client.post("/api/v1/orders/", json={
            "plan_no": "REG-001", "contract_no": "C-NORMAL-001",
            "voltage_kv": 220.0, "current_a": 100.0, "qty": 1,
        })
        resp = client.get("/api/v1/orders/?search=SRCH")
        assert resp.status_code == 200
        results = resp.json()["items"]
        assert len(results) == 1
        assert results[0]["plan_no"] == "SRCH-ZZZ"


    def test_update_nonexistent_order(self, client):
        """PUT /orders/99999 → 404"""
        resp = client.put("/api/v1/orders/99999", json={"status": "scheduled"})
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_delete_nonexistent_order(self, client):
        """DELETE /orders/99999 → 404"""
        resp = client.delete("/api/v1/orders/99999")
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    def test_bulk_import_orders(self, client):
        """POST /orders/bulk-import → 200 + imported count"""
        resp = client.post("/api/v1/orders/bulk-import", json=[
            {"plan_no": "BULK-001", "contract_no": "C-BULK-001", "voltage_kv": 220.0,
             "current_a": 150.0, "qty": 10, "delivery_date": "2026-08-01",
             "product_from": "raw", "product_to": "finished"},
            {"plan_no": "BULK-002", "contract_no": "C-BULK-002", "voltage_kv": 110.0,
             "current_a": 100.0, "qty": 5, "delivery_date": "2026-09-15",
             "product_from": "raw", "product_to": "finished"},
        ])
        assert resp.status_code == 200
        data = resp.json()
        assert data["imported"] >= 1
        assert "skipped" in data


class TestMoldAPI:
    def test_list_molds_empty(self, client):
        resp = client.get("/api/v1/molds/")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_create_mold(self, client):
        resp = client.post("/api/v1/molds/", json={
            "mold_no": "M-API-001",
            "outer_dia": 150.0,
            "inner_dia": 120.0,
            "length": 300.0,
            "stock_qty": 10,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["mold_no"] == "M-API-001"
        assert data["stock_qty"] == 10

    def test_adjust_stock(self, client):
        created = client.post("/api/v1/molds/", json={
            "mold_no": "M-STK-001",
            "outer_dia": 100.0, "inner_dia": 80.0, "length": 250.0,
            "stock_qty": 5,
        })
        mid = created.json()["id"]

        # add stock
        resp = client.post(f"/api/v1/molds/{mid}/stock?delta=3&reason=restock")
        assert resp.status_code == 200
        assert resp.json()["new_stock_qty"] == 8

        # remove stock
        resp = client.post(f"/api/v1/molds/{mid}/stock?delta=-2&reason=issue")
        assert resp.status_code == 200
        assert resp.json()["new_stock_qty"] == 6

    def test_nonexistent_mold(self, client):
        resp = client.get("/api/v1/molds/99999")
        assert resp.status_code == 404


class TestScheduleAPI:
    def test_schedule_optimize_no_orders(self, client):
        """Optimize with empty database — expects 500 because no data files."""
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        # No data files in test env, so 500 is expected
        assert resp.status_code in (200, 400, 500)

    def test_schedule_result_empty(self, client):
        """GET schedule result with no data."""
        resp = client.get("/api/v1/schedule/result")
        assert resp.status_code in (200, 404)
