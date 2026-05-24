"""Process Steps API tests — full CRUD + filtering"""
import pytest


def _create_step(client, **overrides):
    defaults = {
        "step_no": 1,
        "step_name": "繞線",
        "department": "繞線組",
        "team": "A班",
        "process_type": "coil",
        "calc_basis": "qty",
        "h10": 1.5,
        "h24": 2.0,
        "h36": 2.5,
        "h40": 3.0,
    }
    defaults.update(overrides)
    return client.post("/api/v1/process-steps/", json=defaults)


class TestListProcessSteps:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/process-steps/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    def test_list_with_data(self, client):
        _create_step(client, step_no=10, step_name="裁切")
        _create_step(client, step_no=20, step_name="組裝")

        resp = client.get("/api/v1/process-steps/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2

    def test_list_pagination(self, client):
        for i in range(5):
            _create_step(client, step_no=i * 10, step_name=f"步驟-PG-{i}")

        resp = client.get("/api/v1/process-steps/?skip=0&limit=2")
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["total"] >= 5
        assert data["skip"] == 0
        assert data["limit"] == 2

    def test_list_filter_by_department(self, client):
        _create_step(client, step_no=1, step_name="繞線", department="繞線組")
        _create_step(client, step_no=2, step_name="組裝", department="組裝組")

        resp = client.get("/api/v1/process-steps/?department=繞線組")
        data = resp.json()
        assert data["total"] >= 1
        assert all(item["department"] == "繞線組" for item in data["items"])

    def test_list_filter_by_process_type(self, client):
        _create_step(client, step_no=1, step_name="乾燥", process_type="drying")
        _create_step(client, step_no=2, step_name="測試", process_type="testing")

        resp = client.get("/api/v1/process-steps/?process_type=testing")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["process_type"] == "testing"


class TestDepartments:
    def test_departments_empty(self, client):
        resp = client.get("/api/v1/process-steps/departments")
        assert resp.status_code == 200
        assert isinstance(resp.json()["departments"], list)

    def test_departments_with_data(self, client):
        _create_step(client, step_no=1, department="組裝組")
        _create_step(client, step_no=2, department="繞線組")
        _create_step(client, step_no=3, department="組裝組")  # duplicate dept

        resp = client.get("/api/v1/process-steps/departments")
        assert resp.status_code == 200
        depts = resp.json()["departments"]
        assert "組裝組" in depts
        assert "繞線組" in depts


class TestCount:
    def test_count_empty(self, client):
        resp = client.get("/api/v1/process-steps/count")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 0

    def test_count_with_data(self, client):
        _create_step(client, step_no=1)
        _create_step(client, step_no=2)
        _create_step(client, step_no=3)

        resp = client.get("/api/v1/process-steps/count")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 3


class TestGetDetail:
    def test_get_existing(self, client):
        created = _create_step(client, step_no=100, step_name="特殊步驟")
        sid = created.json()["id"]

        resp = client.get(f"/api/v1/process-steps/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["step_name"] == "特殊步驟"
        assert data["step_no"] == 100

    def test_get_nonexistent(self, client):
        resp = client.get("/api/v1/process-steps/99999")
        assert resp.status_code == 404


class TestCreate:
    def test_create_success(self, client):
        resp = _create_step(client, step_no=5, step_name="品質檢驗", department="品管組",
                            team="B班", process_type="inspection",
                            h10=0.5, h24=1.0, h36=1.5, h40=2.0)
        assert resp.status_code == 201
        data = resp.json()
        assert data["step_name"] == "品質檢驗"
        assert data["department"] == "品管組"
        assert data["team"] == "B班"
        assert data["h10"] == 0.5
        assert data["h40"] == 2.0

    def test_create_default_hours(self, client):
        """Default h values should be 0."""
        resp = _create_step(client, step_no=1, step_name="僅名稱")
        assert resp.status_code == 201
        data = resp.json()
        assert data["h10"] == 1.5  # we set it in helper
        # Test without hours explicitly — call directly
        resp2 = client.post("/api/v1/process-steps/", json={
            "step_no": 2, "step_name": "無工時步驟",
        })
        assert resp2.status_code == 201
        d2 = resp2.json()
        assert d2["h10"] == 0
        assert d2["h24"] == 0


class TestUpdate:
    def test_update_existing(self, client):
        created = _create_step(client, step_no=10, step_name="舊名稱")
        sid = created.json()["id"]

        resp = client.put(f"/api/v1/process-steps/{sid}", json={
            "step_name": "新名稱", "h10": 5.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["step_name"] == "新名稱"
        assert data["h10"] == 5.0
        # unchanged fields should stay
        assert data["step_no"] == 10

    def test_update_nonexistent(self, client):
        resp = client.put("/api/v1/process-steps/99999", json={"step_name": "Ghost"})
        assert resp.status_code == 404


class TestDelete:
    def test_delete_existing(self, client):
        created = _create_step(client, step_no=50)
        sid = created.json()["id"]

        resp = client.delete(f"/api/v1/process-steps/{sid}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True
        assert resp.json()["step_id"] == sid

        # Verify gone
        resp2 = client.get(f"/api/v1/process-steps/{sid}")
        assert resp2.status_code == 404

    def test_delete_nonexistent(self, client):
        resp = client.delete("/api/v1/process-steps/99999")
        assert resp.status_code == 404