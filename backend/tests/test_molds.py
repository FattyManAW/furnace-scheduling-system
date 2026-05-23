"""Molds API edge-case tests — low_stock, duplicate, 404s, count"""
import pytest


class TestMoldEdgeCases:
    def test_molds_count_empty(self, client):
        resp = client.get("/api/v1/molds/count")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_molds_count_with_data(self, client):
        client.post("/api/v1/molds/", json={
            "mold_no": "M-CNT-001", "outer_dia": 100.0, "inner_dia": 80.0,
            "length": 200.0, "stock_qty": 3,
        })
        client.post("/api/v1/molds/", json={
            "mold_no": "M-CNT-002", "outer_dia": 120.0, "inner_dia": 100.0,
            "length": 250.0, "stock_qty": 5,
        })
        resp = client.get("/api/v1/molds/count")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_create_duplicate_mold_no(self, client):
        """Should return 400 when mold_no already exists."""
        client.post("/api/v1/molds/", json={
            "mold_no": "M-DUP-001", "outer_dia": 100.0, "inner_dia": 80.0,
            "length": 200.0, "stock_qty": 1,
        })
        resp = client.post("/api/v1/molds/", json={
            "mold_no": "M-DUP-001", "outer_dia": 200.0, "inner_dia": 180.0,
            "length": 300.0, "stock_qty": 2,
        })
        assert resp.status_code == 400
        assert "已存在" in resp.json()["detail"]

    def test_get_nonexistent_mold(self, client):
        resp = client.get("/api/v1/molds/99999")
        assert resp.status_code == 404

    def test_update_nonexistent_mold(self, client):
        resp = client.put("/api/v1/molds/99999", json={
            "outer_dia": 999.0,
        })
        assert resp.status_code == 404

    def test_delete_nonexistent_mold(self, client):
        resp = client.delete("/api/v1/molds/99999")
        assert resp.status_code == 404

    def test_adjust_stock_nonexistent(self, client):
        resp = client.post("/api/v1/molds/99999/stock?delta=5")
        assert resp.status_code == 404

    def test_list_with_low_stock_filter(self, client):
        """low_stock=True should only return molds with stock_qty < threshold."""
        client.post("/api/v1/molds/", json={
            "mold_no": "M-LOW-001", "outer_dia": 100.0, "inner_dia": 80.0,
            "length": 200.0, "stock_qty": 2,  # below threshold (usually 3)
        })
        client.post("/api/v1/molds/", json={
            "mold_no": "M-HIGH-001", "outer_dia": 120.0, "inner_dia": 100.0,
            "length": 250.0, "stock_qty": 50,
        })

        resp = client.get("/api/v1/molds/?low_stock=true")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        mold_nos = [m["mold_no"] for m in items]
        assert "M-LOW-001" in mold_nos

    def test_update_mold_success(self, client):
        """Full update flow — create then modify."""
        created = client.post("/api/v1/molds/", json={
            "mold_no": "M-UPD-001", "outer_dia": 100.0, "inner_dia": 80.0,
            "length": 200.0, "stock_qty": 5, "location": "A區",
            "status": "available",
        })
        mid = created.json()["id"]

        resp = client.put(f"/api/v1/molds/{mid}", json={
            "outer_dia": 110.0,
            "location": "B區",
            "status": "in_use",
            "notes": "更新備註",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["outer_dia"] == 110.0
        assert data["location"] == "B區"
        assert data["status"] == "in_use"
        assert data["notes"] == "更新備註"
        # unchanged fields should persist
        assert data["mold_no"] == "M-UPD-001"
        assert data["inner_dia"] == 80.0

    def test_delete_mold_success(self, client):
        """Delete existing mold."""
        created = client.post("/api/v1/molds/", json={
            "mold_no": "M-DEL-001", "outer_dia": 100.0, "inner_dia": 80.0,
            "length": 200.0, "stock_qty": 1,
        })
        mid = created.json()["id"]

        resp = client.delete(f"/api/v1/molds/{mid}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify gone
        resp2 = client.get(f"/api/v1/molds/{mid}")
        assert resp2.status_code == 404

    def test_get_mold_detail(self, client):
        """Get existing mold by ID."""
        created = client.post("/api/v1/molds/", json={
            "mold_no": "M-GET-001", "outer_dia": 150.0, "inner_dia": 130.0,
            "length": 350.0, "stock_qty": 8,
        })
        mid = created.json()["id"]

        resp = client.get(f"/api/v1/molds/{mid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mold_no"] == "M-GET-001"
        assert data["outer_dia"] == 150.0

    def test_adjust_stock_with_reason(self, client):
        """Adjust stock with explicit reason and verify response."""
        created = client.post("/api/v1/molds/", json={
            "mold_no": "M-STK-REASON", "outer_dia": 100.0, "inner_dia": 80.0,
            "length": 200.0, "stock_qty": 10,
        })
        mid = created.json()["id"]

        resp = client.post(f"/api/v1/molds/{mid}/stock?delta=-3&reason=報廢處理")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mold_no"] == "M-STK-REASON"
        assert data["new_stock_qty"] == 7
        assert data["delta"] == -3
        assert data["reason"] == "報廢處理"