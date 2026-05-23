"""Kilns API integration tests"""
import json


class TestKilnAPI:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/kilns/")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_create_kiln(self, client):
        resp = client.post("/api/v1/kilns/", json={
            "kiln_no": "K-API-001",
            "name": "Test Kiln 1",
            "inner_dia": 800.0,
            "height": 1200.0,
            "schemes": {
                "標準": {"upper": {"od": 470, "id": 300, "len": 1000, "qty": 2},
                        "lower": {"od": 470, "id": 300, "len": 1000, "qty": 2}},
            },
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["kiln_no"] == "K-API-001"
        assert data["inner_dia"] == 800.0
        assert "id" in data

    def test_create_duplicate_kiln(self, client):
        client.post("/api/v1/kilns/", json={
            "kiln_no": "K-DUP-001", "name": "Dup Kiln",
            "inner_dia": 800.0, "height": 1200.0,
        })
        resp = client.post("/api/v1/kilns/", json={
            "kiln_no": "K-DUP-001", "name": "Dup Kiln 2",
            "inner_dia": 700.0, "height": 1100.0,
        })
        assert resp.status_code == 409

    def test_get_kiln_by_id(self, client):
        created = client.post("/api/v1/kilns/", json={
            "kiln_no": "K-GET-001", "name": "Get Test",
            "inner_dia": 900.0, "height": 1300.0,
        })
        kid = created.json()["id"]
        resp = client.get(f"/api/v1/kilns/{kid}")
        assert resp.status_code == 200
        assert resp.json()["kiln_no"] == "K-GET-001"

    def test_get_nonexistent_kiln(self, client):
        resp = client.get("/api/v1/kilns/9999")
        assert resp.status_code == 404

    def test_update_kiln(self, client):
        created = client.post("/api/v1/kilns/", json={
            "kiln_no": "K-UPD-001", "name": "Old Name",
            "inner_dia": 800.0, "height": 1200.0,
        })
        kid = created.json()["id"]
        resp = client.put(f"/api/v1/kilns/{kid}", json={
            "name": "Updated Name",
            "inner_dia": 850.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["inner_dia"] == 850.0

    def test_update_nonexistent_kiln(self, client):
        resp = client.put("/api/v1/kilns/9999", json={"name": "Ghost"})
        assert resp.status_code == 404

    def test_delete_kiln(self, client):
        created = client.post("/api/v1/kilns/", json={
            "kiln_no": "K-DEL-001", "name": "Delete Me",
            "inner_dia": 700.0, "height": 1100.0,
        })
        kid = created.json()["id"]
        resp = client.delete(f"/api/v1/kilns/{kid}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_delete_nonexistent_kiln(self, client):
        resp = client.delete("/api/v1/kilns/9999")
        assert resp.status_code == 404

    def test_kilns_count(self, client):
        client.post("/api/v1/kilns/", json={
            "kiln_no": "K-CNT-001", "name": "Count 1",
            "inner_dia": 800.0, "height": 1200.0,
        })
        client.post("/api/v1/kilns/", json={
            "kiln_no": "K-CNT-002", "name": "Count 2",
            "inner_dia": 800.0, "height": 1200.0,
        })
        resp = client.get("/api/v1/kilns/count")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_list_kilns_with_schemes(self, client):
        schemes = {
            "方案A": {"upper": {"od": 470, "id": 300, "len": 1000, "qty": 2},
                     "lower": {"od": 470, "id": 300, "len": 1000, "qty": 1}},
        }
        client.post("/api/v1/kilns/", json={
            "kiln_no": "K-SCHEMES-001", "name": "Has Schemes",
            "inner_dia": 1000.0, "height": 1500.0,
            "schemes": schemes,
        })
        resp = client.get("/api/v1/kilns/")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) > 0
        found = [k for k in items if k["kiln_no"] == "K-SCHEMES-001"]
        assert len(found) == 1
        assert found[0]["schemes"] == schemes
