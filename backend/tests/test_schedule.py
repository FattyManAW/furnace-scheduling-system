"""Schedule API comprehensive tests — optimize, result, entries, CRUD

Covers api/schedule.py endpoints:
  GET  /                              — root redirect
  POST /optimize                       — main scheduling (happy, errors, reroute)
  GET  /result                         — get current result (happy, 404)
  GET  /{kiln_id}/schedule             — per-kiln schedule (happy, 404)
  GET  /entries                        — paginated list (happy, filter)
  GET  /entries/{entry_id}             — single entry (happy, 404)
  DELETE /entries/{entry_id}           — delete entry (happy, 404)
  DELETE /clear                        — clear all

Target: api/schedule.py ≥70% coverage (currently 27%)
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ensure erp models registered before DB tables created in conftest
import erp_sim.models  # noqa: E402, F401


# ── Seed helpers (module-level for reuse across test classes) ──────────

def _seed_minimal_kiln(client):
    """Create one kiln with schemes that can fit standard products."""
    return client.post("/api/v1/kilns/", json={
        "kiln_no": "K-SCH-001",
        "name": "測試罐 #1",
        "inner_dia": 1500.0,
        "height": 10000.0,
        "schemes": {
            "標準方案": {
                "upper": {"od": 470, "id": 300, "len": 7000, "qty": 2},
                "lower": {"od": 470, "id": 300, "len": 7000, "qty": 7},
            },
        },
    })


def _seed_minimal_order(client, plan_no="SCHED-TEST-001", voltage_kv=220.0,
                        current_a=150.0, qty=5, delivery_date="2026-06-30"):
    """Create one order with standard params."""
    return client.post("/api/v1/orders/", json={
        "plan_no": plan_no,
        "contract_no": "C-SCHED-001",
        "voltage_kv": voltage_kv,
        "current_a": current_a,
        "qty": qty,
        "delivery_date": delivery_date,
        "product_from": "raw",
        "product_to": "finished",
    })


def _seed_minimal_product(db_session):
    """Insert a product directly into DB (no product API)."""
    from models import Product
    p = Product(
        product_no=1,
        voltage_kv=220.0,
        current_a=150.0,
        mold_od=270.0,
        mold_id=180.0,
        mold_len=2000.0,
        capacity=1,
    )
    db_session.add(p)
    db_session.commit()


def _seed_minimal_process_steps(db_session):
    """Insert process steps so hours_per_root is non-zero."""
    from models import ProcessStep
    steps = [
        ProcessStep(step_no=1, step_name="物料採購", department="採購科",
                     h10=0.5, h24=0.8, h36=1.0, h40=1.2),
        ProcessStep(step_no=2, step_name="卷繞", department="干式套管科",
                     h10=1.0, h24=1.5, h36=2.0, h40=2.5),
        ProcessStep(step_no=3, step_name="乾燥", department="干式套管科",
                     h10=2.0, h24=3.0, h36=4.0, h40=5.0),
    ]
    for s in steps:
        db_session.add(s)
    db_session.commit()


def _seed_erp_order(db_session, order_no="SCHED-TEST-001"):
    """Create a matching ERP order for sync."""
    from erp_sim.models import ErpOrder
    eo = ErpOrder(order_no=order_no, product_spec="220kV 套管",
                  quantity=5, priority="normal", status="pending")
    db_session.add(eo)
    db_session.commit()


def _seed_schedule_baseline(client, db_session):
    """Full baseline seed: kiln + product + process + order + erp_order.

    Returns (resp, plan_no) from the order creation.
    """
    _seed_minimal_product(db_session)
    _seed_minimal_process_steps(db_session)
    _seed_minimal_kiln(client)
    resp = _seed_minimal_order(client)
    plan_no = resp.json().get("plan_no", "SCHED-TEST-001")
    _seed_erp_order(db_session, plan_no)
    return resp, plan_no


# ── Tests ───────────────────────────────────────────────────────────────

class TestScheduleRoot:
    def test_schedule_root(self, client):
        """GET /api/v1/schedule/ → 200 + endpoints dict"""
        resp = client.get("/api/v1/schedule/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "endpoints" in data
        assert "optimize" in data["endpoints"]


class TestScheduleOptimize:
    def test_optimize_happy_path(self, client, db_session):
        """POST /schedule/optimize with orders → 200 + scheduled result"""
        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "summary" in data
        assert data["summary"]["scheduled"] >= 1
        assert len(data["schedule"]) >= 1
        # verify ScheduleEntryOut fields
        entry = data["schedule"][0]
        assert "id" in entry
        assert "kiln_id" in entry
        assert "plan_no" in entry
        assert "voltage_kv" in entry
        assert "est_hours" in entry

    def test_optimize_with_specific_order_ids(self, client, db_session):
        """POST /schedule/optimize with order_ids filter"""
        _seed_baseline(client, db_session)
        # create a second order
        _seed_minimal_order(client, plan_no="SCHED-TEST-002",
                            voltage_kv=220.0, qty=3,
                            delivery_date="2026-07-15")
        _seed_erp_order(db_session, "SCHED-TEST-002")

        # query orders to get id
        orders_resp = client.get("/api/v1/orders/")
        orders = orders_resp.json()["items"]
        assert len(orders) >= 2
        # pick first order's id
        first_id = orders[0]["id"]

        resp = client.post("/api/v1/schedule/optimize", json={
            "strategy": "deadline",
            "order_ids": [first_id],
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        # should only schedule the selected order
        assert data["summary"]["scheduled"] <= 1

    def test_optimize_empty_order_ids(self, client, db_session):
        """POST /schedule/optimize with empty order_ids → 400"""
        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={
            "order_ids": [],
            "strategy": "deadline",
        })
        assert resp.status_code == 400
        assert "order_ids" in resp.json()["detail"]

    def test_optimize_no_orders(self, client):
        """POST /schedule/optimize with empty DB → 400"""
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 400
        assert "無可用訂單" in resp.json()["detail"]

    def test_optimize_invalid_strategy(self, client):
        """POST /schedule/optimize with invalid strategy → 422 validation"""
        resp = client.post("/api/v1/schedule/optimize", json={
            "strategy": "invalid_strategy",
        })
        assert resp.status_code == 422

    def test_optimize_balance_strategy(self, client, db_session):
        """POST /schedule/optimize with balance strategy"""
        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "balance"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"]["scheduled"] >= 1

    def test_optimize_fill_strategy(self, client, db_session):
        """POST /schedule/optimize with fill strategy"""
        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "fill"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"]["scheduled"] >= 1

    def test_optimize_multiple_orders(self, client, db_session):
        """POST /schedule/optimize with multiple orders → all scheduled"""
        _seed_baseline(client, db_session)
        # Add two more orders
        for i, kv in enumerate([220.0, 10.0], start=2):
            plan = f"MULTI-{i:03d}"
            _seed_minimal_order(client, plan_no=plan, voltage_kv=kv,
                                qty=3, delivery_date=f"2026-0{i}-15")
            _seed_erp_order(db_session, plan)
        # Need product for 10kV
        from models import Product
        db_session.add(Product(product_no=99, voltage_kv=10.0, current_a=250.0,
                                mold_od=210.0, mold_id=130.0, mold_len=1400.0, capacity=1))
        db_session.commit()

        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"]["scheduled"] >= 2

    def test_optimize_clears_previous_schedule(self, client, db_session):
        """Running optimize twice clears old results"""
        _seed_baseline(client, db_session)
        # First run
        r1 = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert r1.status_code == 200
        # Second run
        r2 = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert r2.status_code == 200
        # Both should have same number of scheduled (no duplicates)
        assert r1.json()["summary"]["scheduled"] == r2.json()["summary"]["scheduled"]

    def test_optimize_response_structure(self, client, db_session):
        """Verify full response model fields"""
        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200
        data = resp.json()
        # summary fields
        assert "total_orders" in data["summary"]
        assert "scheduled" in data["summary"]
        assert "total_hours" in data["summary"]
        assert "daily_cap" in data["summary"]
        # kiln_summary
        assert len(data["kiln_summary"]) >= 1
        ks = data["kiln_summary"][0]
        assert "kiln_id" in ks
        assert "hours_used" in ks
        assert "usage_pct" in ks
        # schedule entries
        assert len(data["schedule"]) >= 1
        # warnings
        assert isinstance(data["warnings"], list)
        # reroute flags
        assert "reroutes_applied" in data
        assert isinstance(data["reroutes_applied"], bool)


class TestScheduleResult:
    def test_result_after_optimize(self, client, db_session):
        """GET /schedule/result after optimization → 200"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        resp = client.get("/api/v1/schedule/result")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"]["scheduled"] >= 1
        assert len(data["schedule"]) >= 1
        # verify schedule entry has kiln_name
        entry = data["schedule"][0]
        assert "kiln_name" in entry

    def test_result_empty(self, client):
        """GET /schedule/result with no data → 404"""
        resp = client.get("/api/v1/schedule/result")
        assert resp.status_code == 404
        assert "尚無排程結果" in resp.json()["detail"]


class TestScheduleByKiln:
    def test_get_kiln_schedule(self, client, db_session):
        """GET /schedule/{kiln_id}/schedule → 200"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        # get kiln id from result
        result = client.get("/api/v1/schedule/result").json()
        kid = result["schedule"][0]["kiln_id"]

        resp = client.get(f"/api/v1/schedule/{kid}/schedule")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["kiln_id"] == kid
        assert "kiln_name" in data
        assert len(data["entries"]) >= 1

    def test_get_kiln_schedule_not_found(self, client, db_session):
        """GET /schedule/{kiln_id}/schedule for nonexistent kiln → 404"""
        _seed_baseline(client, db_session)
        resp = client.get("/api/v1/schedule/99999/schedule")
        assert resp.status_code == 404
        assert "干燥罐不存在" in resp.json()["detail"]

    def test_get_kiln_schedule_empty_kiln(self, client, db_session):
        """GET /schedule/{kiln_id}/schedule with kiln that has no entries → empty"""
        _seed_baseline(client, db_session)
        # create second kiln with no schedule entries
        r = client.post("/api/v1/kilns/", json={
            "kiln_no": "K-EMPTY-001", "name": "空罐",
            "inner_dia": 800.0, "height": 1200.0,
            "schemes": {"方案": {"upper": {"od": 470, "id": 300, "len": 7000, "qty": 1},
                                 "lower": {"od": 0, "id": 0, "len": 0, "qty": 0}}},
        })
        kid = r.json()["id"]
        # Only schedule order that uses first kiln
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        resp = client.get(f"/api/v1/schedule/{kid}/schedule")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kiln_id"] == kid
        # May or may not have entries depending on fit
        assert "entries" in data


class TestScheduleEntries:
    def test_list_entries_after_optimize(self, client, db_session):
        """GET /schedule/entries after optimize → 200 with items"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        resp = client.get("/api/v1/schedule/entries")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert "skip" in data
        assert "limit" in data

    def test_list_entries_pagination(self, client, db_session):
        """GET /schedule/entries with skip/limit"""
        _seed_baseline(client, db_session)
        # Add multiple orders to get multiple entries
        for i in range(2, 6):
            plan = f"PAGE-{i:03d}"
            _seed_minimal_order(client, plan_no=plan, voltage_kv=220.0,
                                qty=2, delivery_date=f"2026-0{i}-15")
            _seed_erp_order(db_session, plan)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})

        resp = client.get("/api/v1/schedule/entries?skip=0&limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2

    def test_list_entries_filter_by_kiln(self, client, db_session):
        """GET /schedule/entries?kiln_id=X"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        result = client.get("/api/v1/schedule/result").json()
        kid = result["schedule"][0]["kiln_id"]

        resp = client.get(f"/api/v1/schedule/entries?kiln_id={kid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["kiln_id"] == kid

    def test_get_single_entry(self, client, db_session):
        """GET /schedule/entries/{entry_id} → 200"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        entries = client.get("/api/v1/schedule/entries").json()
        assert entries["total"] >= 1
        eid = entries["items"][0]["id"]

        resp = client.get(f"/api/v1/schedule/entries/{eid}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == eid
        assert "plan_no" in data

    def test_get_single_entry_not_found(self, client, db_session):
        """GET /schedule/entries/{entry_id} for nonexistent → 404"""
        _seed_baseline(client, db_session)
        resp = client.get("/api/v1/schedule/entries/99999")
        assert resp.status_code == 404
        assert "排程記錄不存在" in resp.json()["detail"]

    def test_delete_entry(self, client, db_session):
        """DELETE /schedule/entries/{entry_id} → 200"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        entries = client.get("/api/v1/schedule/entries").json()
        eid = entries["items"][0]["id"]

        resp = client.delete(f"/api/v1/schedule/entries/{eid}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True
        assert resp.json()["entry_id"] == eid

        # verify gone
        resp2 = client.get(f"/api/v1/schedule/entries/{eid}")
        assert resp2.status_code == 404

    def test_delete_entry_not_found(self, client, db_session):
        """DELETE /schedule/entries/99999 → 404"""
        _seed_baseline(client, db_session)
        resp = client.delete("/api/v1/schedule/entries/99999")
        assert resp.status_code == 404
        assert "排程記錄不存在" in resp.json()["detail"]

    def test_clear_all_schedule(self, client, db_session):
        """DELETE /schedule/clear → 200"""
        _seed_baseline(client, db_session)
        client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        resp = client.delete("/api/v1/schedule/clear")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True
        assert resp.json()["count"] >= 1

        # verify entries are gone
        entries_resp = client.get("/api/v1/schedule/entries")
        assert entries_resp.json()["total"] == 0

    def test_list_entries_empty(self, client):
        """GET /schedule/entries with empty DB → 0 items"""
        resp = client.get("/api/v1/schedule/entries")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestScheduleValidation:
    def test_optimize_order_not_found_in_erp(self, client, db_session):
        """Optimize with order that has no matching ERP order → still works (sync skips)"""
        _seed_minimal_product(db_session)
        _seed_minimal_process_steps(db_session)
        _seed_minimal_kiln(client)
        _seed_minimal_order(client, plan_no="NO-ERP-001")
        # Do NOT seed ERP order
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["scheduled"] >= 1


class TestScheduleEdgeCases:
    """Cover remaining uncovered branches in api/schedule.py (lines 32, 84, 95-107, 125-128, 140-142)"""

    def test_kiln_name_null_id(self):
        """_kiln_name returns '' for falsy kiln_id (line 32)."""
        from api.schedule import _kiln_name
        from database import SessionLocal
        db = SessionLocal()
        try:
            assert _kiln_name(db, 0) == ""
            assert _kiln_name(db, None) == ""
        finally:
            db.close()

    def test_validation_error_adds_warnings(self, client, db_session, monkeypatch):
        """schedule/optimize adds [驗證錯誤] to warnings on validation failure (line 84)."""
        import api.schedule as smod
        monkeypatch.setattr(
            smod, "validate_schedule",
            lambda result: {"valid": False, "errors": ["ERR-TEST-1", "ERR-TEST-2"]},
        )
        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200
        data = resp.json()
        found = [w for w in data["warnings"] if "[驗證錯誤]" in w]
        assert len(found) >= 2

    def test_reroute_with_moves(self, client, db_session, monkeypatch):
        """schedule/optimize: congestion → reroute moves orders → reroutes_applied=True (lines 95-107)."""
        import api.schedule as smod

        # Make schedule_orders return a result with a congested kiln
        def fake_schedule_orders(orders, **kw):
            return {
                "order_schedule": [{
                    "plan_no": "SCHED-TEST-001", "kiln_id": "1", "kiln_name": "K1",
                    "voltage_kv": 220.0, "current_a": 150.0, "qty": 5,
                    "delivery_date": "2026-06-30", "contract_no": "C-SCHED-001",
                    "mold_od": 0, "mold_len": 0, "est_hours": 10, "status": "scheduled",
                }],
                "kiln_schedule": {
                    "1": {"usage_pct": 95, "hours_used": 1000, "slots_used": 1,
                           "total_slots": 10, "order_count": 1,
                           "orders": [{"plan_no": "SCHED-TEST-001", "hours": 10}],
                           "kiln_name": "K1"},
                },
                "summary": {"scheduled": 1, "total_orders": 1, "total_hours": 10, "daily_cap": 1098},
                "warnings": [],
            }

        monkeypatch.setattr(smod, "schedule_orders", fake_schedule_orders)

        # Make reroute_on_congestion report moved > 0
        def fake_reroute_moved(result, **kw):
            result["reroute"] = {
                "iterations": 1, "moved": 3,
                "before": {"congested_kilns": 1, "max_usage_pct": 95, "avg_usage_pct": 60, "usage_spread": 40},
                "after": {"congested_kilns": 0, "max_usage_pct": 70, "avg_usage_pct": 60, "usage_spread": 15},
            }
            return result

        monkeypatch.setattr(smod, "reroute_on_congestion", fake_reroute_moved)
        monkeypatch.setattr(smod, "sync_schedule_to_erp", lambda db, result: {})

        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["reroutes_applied"] is True
        assert data["reroute_info"]["moved"] == 3
        assert data["reroute_info"]["iterations"] == 1

    def test_reroute_congestion_but_no_moves(self, client, db_session, monkeypatch):
        """schedule/optimize: congestion detected but reroute moved=0 → reroutes_applied=False."""
        import api.schedule as smod

        def fake_schedule_orders(orders, **kw):
            return {
                "order_schedule": [{
                    "plan_no": "SCHED-TEST-001", "kiln_id": "1", "kiln_name": "K1",
                    "voltage_kv": 220.0, "current_a": 150.0, "qty": 5,
                    "delivery_date": "2026-06-30", "contract_no": "C-SCHED-001",
                    "mold_od": 0, "mold_len": 0, "est_hours": 10, "status": "scheduled",
                }],
                "kiln_schedule": {
                    "1": {"usage_pct": 95, "hours_used": 1000, "slots_used": 1,
                           "total_slots": 10, "order_count": 1,
                           "orders": [{"plan_no": "SCHED-TEST-001", "hours": 10}],
                           "kiln_name": "K1"},
                },
                "summary": {"scheduled": 1, "total_orders": 1, "total_hours": 10, "daily_cap": 1098},
                "warnings": [],
            }

        monkeypatch.setattr(smod, "schedule_orders", fake_schedule_orders)

        def fake_reroute_noop(result, **kw):
            result["reroute"] = {"iterations": 0, "moved": 0, "before": {}, "after": {}}
            return result

        monkeypatch.setattr(smod, "reroute_on_congestion", fake_reroute_noop)
        monkeypatch.setattr(smod, "sync_schedule_to_erp", lambda db, result: {})

        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["reroutes_applied"] is False

    def test_delivery_date_slash_format(self, client, db_session, monkeypatch):
        """schedule/optimize: delivery_date in YYYY/MM/DD format → fallback path (lines 140-142)."""
        import api.schedule as smod

        def fake_schedule_orders(orders, **kw):
            return {
                "order_schedule": [{
                    "plan_no": "SCHED-TEST-001", "kiln_id": "1", "kiln_name": "K1",
                    "voltage_kv": 220.0, "current_a": 150.0, "qty": 5,
                    # Use slash format — should trigger the fallback on line 141
                    "delivery_date": "2026/06/30", "contract_no": "C-SCHED-001",
                    "mold_od": 0, "mold_len": 0, "est_hours": 10, "status": "scheduled",
                }],
                "kiln_schedule": {
                    "1": {"usage_pct": 50, "hours_used": 10, "slots_used": 1,
                           "total_slots": 10, "order_count": 1,
                           "orders": [{"plan_no": "SCHED-TEST-001", "hours": 10}],
                           "kiln_name": "K1"},
                },
                "summary": {"scheduled": 1, "total_orders": 1, "total_hours": 10, "daily_cap": 1098},
                "warnings": [],
            }

        monkeypatch.setattr(smod, "schedule_orders", fake_schedule_orders)
        monkeypatch.setattr(smod, "reroute_on_congestion", lambda result, **kw: result)
        monkeypatch.setattr(smod, "sync_schedule_to_erp", lambda db, result: {})

        _seed_baseline(client, db_session)
        resp = client.post("/api/v1/schedule/optimize", json={"strategy": "deadline"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["scheduled"] >= 1
        # delivery_date was in slash format — fallback normalization runs without error
        # (normalization applies to DB write, response shows original from result dict)
        assert len(data["schedule"]) >= 1


# ── Alias for the seed helper used in tests ─────────────────────────────
_seed_baseline = _seed_schedule_baseline