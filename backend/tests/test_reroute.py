"""Test: reroute_on_congestion hook — before/after WIP 對比

使用 furnace-scheduling-system 真實 DB + optimizer 數據
驗證：congestion detect → redirect → before/after report
"""
from __future__ import annotations

import json
import os
import sys

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, backend_dir)

from engine.data_layer import load_all_optimizer_data
from engine.optimizer import quality_report, schedule_orders
from engine.reroute import reroute_on_congestion, reroute_report
from seed_data import seed_all

from database import Base, SessionLocal, engine

Base.metadata.create_all(bind=engine)


def _run_reroute_integration():
    """Helper: seed → schedule → detect → reroute → report. Returns full result dict."""
    db = SessionLocal()
    try:
        seed_all()

        # Load data
        products_by_voltage, kilns_data, hours_per_root = load_all_optimizer_data(db)

        # Get orders
        from models import Order
        orders = db.query(Order).order_by(Order.id).all()

        order_dicts = []
        for o in orders:
            order_dicts.append({
                "plan_no": o.plan_no,
                "contract_no": o.contract_no,
                "voltage_kv": o.voltage_kv,
                "current_a": o.current_a,
                "qty": o.qty,
                "delivery_date": o.delivery_date or "",
                "product_from": o.product_from,
                "product_to": o.product_to,
            })

        print(f"📊 Loaded {len(order_dicts)} orders, {len(kilns_data)} kilns, {len(products_by_voltage)} voltage groups")
        print(f"   Hours/root: {hours_per_root}")

        # Run optimizer (baseline)
        result = schedule_orders(
            order_dicts,
            products_by_voltage=products_by_voltage,
            kilns_data=kilns_data,
            hours_per_root=hours_per_root,
        )

        report = quality_report(result)
        print(f"\n📈 Baseline quality: score={report['score']}, rate={report['rate']}%, kilns_used={report['kilns_used']}")
        print(f"   Scheduled: {report['scheduled']}, Skipped: {report['skipped']}")

        # Print initial congestion
        ks = result.get("kiln_schedule", {})
        pcts = [k["usage_pct"] for k in ks.values()]
        congested = sum(1 for p in pcts if p >= 85)
        print(f"   Congested kilns (≥85%): {congested}/{len(ks)}")
        print(f"   Max usage: {max(pcts):.1f}%, Avg: {sum(pcts)/len(pcts):.1f}%")

        # Apply reroute
        rerouted = reroute_on_congestion(
            result,
            kilns_data=kilns_data,
            products_by_voltage=products_by_voltage,
            hours_per_root=hours_per_root,
            congestion_threshold=85.0,
        )

        # Print report
        print(reroute_report(rerouted))

        # Verify reroute stats
        rr = rerouted.get("reroute", {})
        print(f"\n✅ Test complete: {rr.get('moved', 0)} orders rerouted in {rr.get('iterations', 0)} iterations")

        # Verify no data corruption
        total_orders = sum(k.get("order_count", 0) for k in rerouted["kiln_schedule"].values())
        expected = result["summary"]["scheduled"]
        assert total_orders == expected, f"Order count mismatch: {total_orders} vs {expected}"

        return rerouted

    finally:
        db.close()


def test_reroute_before_after():
    """Full integration: seed → schedule → detect → reroute → report"""
    rerouted = _run_reroute_integration()
    rr = rerouted.get("reroute", {})

    # Assert reroute structure is valid
    assert "before" in rr, "Missing before stats"
    assert "after" in rr, "Missing after stats"
    assert "moved" in rr, "Missing moved count"
    assert isinstance(rr["moved"], int), "moved should be int"

    # Assert order count integrity
    total_orders = sum(k.get("order_count", 0) for k in rerouted["kiln_schedule"].values())
    assert total_orders == rerouted["summary"]["scheduled"], \
        f"Order count mismatch: {total_orders} vs {rerouted['summary']['scheduled']}"

    # Assert before/after improvement or no-op
    before = rr["before"]
    after = rr["after"]
    # Moving orders can trade congested kiln count for better spread — both are valid outcomes
    if rr["moved"] > 0:
        # When orders moved, at least one of these should improve:
        # spread narrows, max usage drops, or congested count drops
        spread_improved = after.get("usage_spread", 999) <= before.get("usage_spread", 999)
        max_improved = after.get("max_usage_pct", 999) <= before.get("max_usage_pct", 999)
        congested_improved = after.get("congested_kilns", 999) <= before.get("congested_kilns", 999)
        assert spread_improved or max_improved or congested_improved, \
            f"Reroute should improve at least one metric. Before: {before}, After: {after}"


def test_reroute_field_mapping():
    """Verify reroute handles optimizer field names correctly (mold_id_dia)."""
    db = SessionLocal()
    try:
        seed_all()
        products_by_voltage, kilns_data, hours_per_root = load_all_optimizer_data(db)

        from models import Order
        orders = db.query(Order).order_by(Order.id).all()
        order_dicts = [{
            "plan_no": o.plan_no, "contract_no": o.contract_no,
            "voltage_kv": o.voltage_kv, "current_a": o.current_a,
            "qty": o.qty, "delivery_date": o.delivery_date or "",
            "product_from": o.product_from, "product_to": o.product_to,
        } for o in orders]

        result = schedule_orders(
            order_dicts, products_by_voltage=products_by_voltage,
            kilns_data=kilns_data, hours_per_root=hours_per_root,
        )

        # All scheduled orders should have mold_id_dia key
        for entry in result.get("order_schedule", []):
            assert "mold_id_dia" in entry, f"{entry['plan_no']} missing mold_id_dia"
            assert isinstance(entry["mold_id_dia"], (int, float)), \
                f"{entry['plan_no']} mold_id_dia is not numeric: {entry['mold_id_dia']}"

        # reroute should work without errors even with only mold_id_dia
        rerouted = reroute_on_congestion(
            result, kilns_data=kilns_data,
            products_by_voltage=products_by_voltage,
            hours_per_root=hours_per_root,
        )
        assert "reroute" in rerouted
    finally:
        db.close()


if __name__ == "__main__":
    result = _run_reroute_integration()
    rr = result.get("reroute", {})
    before = rr.get("before", {})
    after = rr.get("after", {})

    # Output JSON for CI
    output = {
        "orders_moved": rr.get("moved", 0),
        "iterations": rr.get("iterations", 0),
        "before": before,
        "after": after,
        "improvement": {
            "max_usage_delta": round(before.get("max_usage_pct", 0) - after.get("max_usage_pct", 0), 1),
            "spread_delta": round(before.get("usage_spread", 0) - after.get("usage_spread", 0), 1),
            "congested_delta": before.get("congested_kilns", 0) - after.get("congested_kilns", 0),
        },
    }
    print("\n📊 CI JSON:")
    print(json.dumps(output, indent=2, ensure_ascii=False))


# ── Unit tests for uncovered branches ───────────────────────────────────

def _make_kiln_schedule(kilns: list[dict]) -> dict:
    """Helper: build kiln_schedule dict from list of {id, usage_pct, hours_used, slots_used, total_slots, orders, ...}"""
    return {
        str(k["id"]): {
            "kiln_name": k.get("name", f"Kiln-{k['id']}"),
            "usage_pct": k.get("usage_pct", 0),
            "hours_used": k.get("hours_used", 0),
            "slots_used": k.get("slots_used", 0),
            "total_slots": k.get("total_slots", 10),
            "order_count": len(k.get("orders", [])),
            "orders": k.get("orders", []),
        }
        for k in kilns
    }


class TestDetectCongestion:
    """Unit tests for detect_congestion — covers edge cases."""

    def test_no_congestion(self):
        """detect_congestion returns empty when all kilns under threshold."""
        from engine.reroute import detect_congestion
        ks = _make_kiln_schedule([
            {"id": 1, "usage_pct": 50, "hours_used": 120, "orders": [{"plan_no": "A"}]},
            {"id": 2, "usage_pct": 70, "hours_used": 168, "orders": []},
        ])
        result = detect_congestion(ks, threshold_pct=85.0)
        assert result == []

    def test_congested_sorted_desc(self):
        """detect_congestion returns sorted by usage_pct descending."""
        from engine.reroute import detect_congestion
        ks = _make_kiln_schedule([
            {"id": 1, "usage_pct": 90, "hours_used": 216, "orders": [{"plan_no": "X"}]},
            {"id": 2, "usage_pct": 95, "hours_used": 228, "orders": [{"plan_no": "Y"}]},
        ])
        result = detect_congestion(ks, threshold_pct=85.0)
        assert len(result) == 2
        assert result[0]["usage_pct"] == 95
        assert result[1]["usage_pct"] == 90

    def test_empty_kiln_schedule(self):
        """detect_congestion handles empty schedule."""
        from engine.reroute import detect_congestion
        result = detect_congestion({})
        assert result == []


class TestFindAlternateKilns:
    """Unit tests for find_alternate_kilns — covers branch conditions."""

    def test_skip_congested_kiln(self, monkeypatch):
        """find_alternate_kilns skips kiln with usage_pct >= max_usage_pct (line 85)."""
        import engine.optimizer as opt
        from engine.reroute import find_alternate_kilns
        # Make fit_score return a low value so kiln would normally qualify
        monkeypatch.setattr(opt, "fit_score", lambda *a, **kw: 0.0)

        order = {"plan_no": "TEST", "voltage_kv": 220, "qty": 5,
                 "mold_od": 270, "mold_len": 2000, "mold_inner_dia": 180}
        kilns_data = {"1": {"id": 1, "name": "K1"}, "2": {"id": 2, "name": "K2"}}
        kiln_schedule = {
            "1": {"usage_pct": 90, "slots_used": 2, "total_slots": 10, "order_count": 2,
                   "orders": [], "hours_used": 216, "kiln_name": "K1"},
            "2": {"usage_pct": 50, "slots_used": 2, "total_slots": 10, "order_count": 2,
                   "orders": [], "hours_used": 120, "kiln_name": "K2"},
        }
        result = find_alternate_kilns(order, kilns_data, kiln_schedule,
                                      max_usage_pct=85.0)
        # K1 (usage 90%) should be skipped; only K2 qualifies
        assert len(result) == 1
        assert result[0]["kiln_id"] == "2"

    def test_skip_full_kiln(self, monkeypatch):
        """find_alternate_kilns skips kiln with no slots (line 73-74)."""
        import engine.optimizer as opt
        from engine.reroute import find_alternate_kilns
        monkeypatch.setattr(opt, "fit_score", lambda *a, **kw: 0.0)

        order = {"plan_no": "TEST", "voltage_kv": 220, "qty": 5,
                 "mold_od": 270, "mold_len": 2000, "mold_inner_dia": 180}
        kilns_data = {"1": {"id": 1, "name": "K1"}}
        kiln_schedule = {
            "1": {"usage_pct": 30, "slots_used": 10, "total_slots": 10,
                   "order_count": 10, "orders": [], "hours_used": 72, "kiln_name": "K1"},
        }
        result = find_alternate_kilns(order, kilns_data, kiln_schedule,
                                      max_usage_pct=85.0)
        assert result == []

    def test_fit_score_too_high_skipped(self, monkeypatch):
        """find_alternate_kilns skips when fit_score >= 999 (line 98)."""
        import engine.optimizer as opt
        from engine.reroute import find_alternate_kilns
        monkeypatch.setattr(opt, "fit_score", lambda *a, **kw: 999.0)

        order = {"plan_no": "TEST", "voltage_kv": 220, "qty": 5,
                 "mold_od": 270, "mold_len": 2000, "mold_inner_dia": 180}
        kilns_data = {"1": {"id": 1, "name": "K1"}}
        kiln_schedule = {
            "1": {"usage_pct": 30, "slots_used": 2, "total_slots": 10,
                   "order_count": 2, "orders": [], "hours_used": 72, "kiln_name": "K1"},
        }
        result = find_alternate_kilns(order, kilns_data, kiln_schedule,
                                      max_usage_pct=85.0)
        assert result == []


class TestRerouteOnCongestionEdges:
    """Edge-case tests for reroute_on_congestion."""

    def test_congested_kiln_empty_orders(self):
        """reroute_on_congestion handles congested kiln with no orders (line 164)."""
        from engine.reroute import reroute_on_congestion
        result = {
            "order_schedule": [],
            "kiln_schedule": {
                "1": {"usage_pct": 90, "hours_used": 216, "slots_used": 5,
                       "total_slots": 10, "order_count": 0, "orders": [],
                       "kiln_name": "K1"},
            },
            "summary": {"scheduled": 0, "total_orders": 0, "total_hours": 0, "daily_cap": 24},
            "warnings": [],
        }
        rerouted = reroute_on_congestion(
            result, kilns_data={}, products_by_voltage={}, hours_per_root={},
            congestion_threshold=85.0,
        )
        # Should not crash; congested kiln has empty orders so nothing to move
        rr = rerouted.get("reroute", {})
        assert rr["moved"] == 0
        assert "before" in rr
        assert "after" in rr

    def test_no_full_order_match(self):
        """reroute_on_congestion: plan_no in summary but not in full orders (line 172)."""
        from engine.reroute import reroute_on_congestion
        result = {
            "order_schedule": [
                {"plan_no": "REAL-ORDER", "voltage_kv": 220, "qty": 5,
                 "mold_od": 270, "mold_len": 2000, "mold_inner_dia": 180,
                 "kiln_id": "1", "est_hours": 10},
            ],
            "kiln_schedule": {
                "1": {"usage_pct": 90, "hours_used": 216, "slots_used": 5,
                       "total_slots": 10, "order_count": 1,
                       "orders": [{"plan_no": "MISSING-ORDER", "hours": 10}],
                       "kiln_name": "K1"},
                "2": {"usage_pct": 40, "hours_used": 96, "slots_used": 2,
                       "total_slots": 10, "order_count": 0, "orders": [],
                       "kiln_name": "K2"},
            },
            "summary": {"scheduled": 1, "total_orders": 1, "total_hours": 10, "daily_cap": 24},
            "warnings": [],
        }
        rerouted = reroute_on_congestion(
            result, kilns_data={}, products_by_voltage={}, hours_per_root={},
            congestion_threshold=85.0,
        )
        rr = rerouted.get("reroute", {})
        assert rr["moved"] == 0

    def test_no_alternate_kilns_found(self, monkeypatch):
        """reroute_on_congestion: order has no viable alternate kilns (line 182)."""
        import engine.optimizer as opt
        from engine.reroute import reroute_on_congestion
        monkeypatch.setattr(opt, "fit_score", lambda *a, **kw: 999.0)  # always unfit

        order_schedule = [
            {"plan_no": "STUCK", "voltage_kv": 220, "qty": 5,
             "mold_od": 270, "mold_len": 2000, "mold_inner_dia": 180,
             "kiln_id": "1", "est_hours": 10},
        ]
        result = {
            "order_schedule": order_schedule,
            "kiln_schedule": {
                "1": {"usage_pct": 95, "hours_used": 228, "slots_used": 5,
                       "total_slots": 10, "order_count": 1,
                       "orders": [{"plan_no": "STUCK", "hours": 10}],
                       "kiln_name": "K1"},
                "2": {"usage_pct": 40, "hours_used": 96, "slots_used": 2,
                       "total_slots": 10, "order_count": 0, "orders": [],
                       "kiln_name": "K2"},
            },
            "summary": {"scheduled": 1, "total_orders": 1, "total_hours": 10, "daily_cap": 24},
            "warnings": [],
        }
        rerouted = reroute_on_congestion(
            result, kilns_data={"2": {"id": 2, "name": "K2"}},
            products_by_voltage={}, hours_per_root={},
            congestion_threshold=85.0,
        )
        rr = rerouted.get("reroute", {})
        assert rr["moved"] == 0

    def test_no_congestion_returns_early(self):
        """reroute_on_congestion: no congestion → early return, 0 iterations."""
        from engine.reroute import reroute_on_congestion
        result = {
            "order_schedule": [],
            "kiln_schedule": {
                "1": {"usage_pct": 50, "hours_used": 120, "slots_used": 5,
                       "total_slots": 10, "order_count": 5, "orders": [{"plan_no": "A"}],
                       "kiln_name": "K1"},
            },
            "summary": {"scheduled": 5, "total_orders": 5, "total_hours": 120, "daily_cap": 24},
            "warnings": [],
        }
        rerouted = reroute_on_congestion(
            result, kilns_data={}, products_by_voltage={}, hours_per_root={},
            congestion_threshold=85.0,
        )
        rr = rerouted.get("reroute", {})
        assert rr["moved"] == 0
        assert rr["iterations"] == 0


class TestRerouteReport:
    """Unit tests for reroute_report."""

    def test_no_reroute_data(self):
        """reroute_report with missing 'reroute' key (line 257)."""
        from engine.reroute import reroute_report
        report = reroute_report({})
        assert "無 reroute 數據" in report

    def test_reroute_report_empty_dict(self):
        """reroute_report with empty reroute dict — still returns the warning (falsy)."""
        from engine.reroute import reroute_report
        report = reroute_report({"reroute": {}})
        # Python: empty dict is falsy → "無 reroute 數據"
        assert isinstance(report, str)
        assert "無 reroute 數據" in report

    def test_reroute_report_no_congestion(self):
        """reroute_report when moved=0 → 'No congestion detected' (line 295)."""
        from engine.reroute import reroute_report
        result = {
            "reroute": {
                "iterations": 1,
                "moved": 0,
                "before": {"congested_kilns": 0, "max_usage_pct": 50, "avg_usage_pct": 50, "usage_spread": 0},
                "after": {"congested_kilns": 0, "max_usage_pct": 50, "avg_usage_pct": 50, "usage_spread": 0},
            }
        }
        report = reroute_report(result)
        assert "No congestion detected" in report or "無 reroute 數據" in report
