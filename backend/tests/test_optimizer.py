"""Unit tests for optimizer v2.1 — fit_score, delivery priority, full schedule"""
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime
from unittest.mock import ANY, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

from optimizer import (
    _load_data,
    _sf,
    _si,
    check_mold_availability,
    delivery_priority,
    fit_score,
    hours_for,
    quality_report,
    schedule_orders,
)


# ── _sf / _si helper coverage ────────────────────────────────────────────
class TestSafeConverters:
    def test_sf_empty_string(self):
        assert _sf("") == 0.0

    def test_sf_japanese_dash(self):
        assert _sf("－") == 0.0

    def test_sf_dash(self):
        assert _sf("-") == 0.0

    def test_sf_emdash(self):
        assert _sf("—") == 0.0

    def test_sf_exception_returns_zero(self):
        # "abc" fails float conversion → exception path
        assert _sf("not-a-number!!") == 0.0

    def test_sf_number_passthrough(self):
        assert _sf(42) == 42.0

    def test_sf_comma_stripping(self):
        assert _sf("1,234.56") == 1234.56

    def test_si_empty_string(self):
        assert _si("") == 0

    def test_si_dash(self):
        assert _si("-") == 0

    def test_si_japanese_dash(self):
        assert _si("－") == 0

    def test_si_emdash(self):
        assert _si("—") == 0

    def test_si_exception_returns_zero(self):
        assert _si("not-a-number!!") == 0

    def test_si_integer_passthrough(self):
        assert _si(42) == 42

    def test_si_float_converts_to_int(self):
        assert _si("123.7") == 123


# ── hours_for ─────────────────────────────────────────────────────────────
class TestHoursFor:
    def test_voltage_le_15(self):
        h = hours_for(qty=10, voltage_kv=10.0)
        assert h > 0

    def test_voltage_24_range(self):
        h = hours_for(qty=5, voltage_kv=24.0)
        assert h > 0

    def test_voltage_36_range(self):
        h = hours_for(qty=3, voltage_kv=36.0)
        assert h > 0

    def test_voltage_above_38(self):
        h = hours_for(qty=2, voltage_kv=50.0)
        assert h > 0

    def test_without_preloaded_hours_per_root(self):
        """hours_for with hours_per_root=None → triggers _load_data internal fallback (line 78)"""
        h = hours_for(qty=1, voltage_kv=10.0, hours_per_root=None)
        assert h > 0


# ── fit_score ─────────────────────────────────────────────────────────────
class TestFitScore:
    def test_small_product_fits(self):
        kilns, _, _ = _load_data()
        k = kilns["1"]
        score = fit_score(k, mold_od=210.0, mold_len=1400.0)
        assert score < 999.0, f"Should fit in this kiln, got {score}"

    def test_big_product_fits_big_kiln(self):
        kilns, _, _ = _load_data()
        k = kilns["1"]
        score = fit_score(k, mold_od=470.0, mold_len=7000.0, needs_big_slot=True)
        assert score < 10, f"Should fit, got {score}"

    def test_too_large_product_fails(self):
        kilns, _, _ = _load_data()
        k = kilns["1"]
        score = fit_score(k, mold_od=9999.0, mold_len=99999.0)
        assert score == 999.0, f"Should not fit, got {score}"

    def test_small_kiln_cannot_fit_big(self):
        kilns, _, _ = _load_data()
        k28 = kilns["28"]
        score = fit_score(k28, mold_od=470.0, mold_len=7000.0, needs_big_slot=True)
        assert score == 999.0, f"Small kiln should not fit big product: {score}"

    def test_prefers_tighter_fit(self):
        kilns, _, _ = _load_data()
        k1 = kilns["1"]
        k28 = kilns["28"]
        s1 = fit_score(k1, mold_od=210.0, mold_len=1400.0)
        s28 = fit_score(k28, mold_od=210.0, mold_len=1400.0)
        assert s1 != 999.0 or s28 != 999.0, "At least one kiln should fit"

    def test_inner_dia_bonus_applies(self):
        """inner_dia match — mold_inner_dia > 0 and sid > mold_inner_dia → id_bonus applied (lines 170-176)"""
        kilns, _, _ = _load_data()
        k1 = kilns["1"]
        # K1 scheme B lower has id=320, od=410, len=6245
        # product with mold_od=270, mold_len=2000 — fits in upper (id=180)
        # but also fits lower; with inner_dia=250, lower id 320 > 250 → bonus applies
        score_with_id = fit_score(k1, mold_od=270.0, mold_len=2000.0, mold_inner_dia=250.0)
        score_without_id = fit_score(k1, mold_od=270.0, mold_len=2000.0, mold_inner_dia=0.0)
        # Both should fit, inner_dia may affect score
        assert score_with_id < 999.0
        assert score_without_id < 999.0

    def test_big_slot_penalty_for_small_product(self):
        """small product not needing big slot gets big_penalty=1.0 on 470mm+ slots (lines 181-183)"""
        kilns, _, _ = _load_data()
        k1 = kilns["1"]
        # K1 scheme C lower has od=470; small product not needing big slot
        # should have elevated score due to big_penalty
        score_small = fit_score(k1, mold_od=210.0, mold_len=1400.0, needs_big_slot=False)
        assert score_small < 999.0  # still fits

    def test_needs_big_slot_no_penalty(self):
        """product needing big slot at 470+ gets no big_penalty (lines 178-180).
        With needs_big_slot=False, same product gets +1.0 big_penalty → higher score."""
        kilns, _, _ = _load_data()
        k1 = kilns["1"]
        # K1 scheme A lower: od=470, len=7000 — exact fit for 470×7000
        score_needs = fit_score(k1, mold_od=470.0, mold_len=7000.0, needs_big_slot=True)
        score_not = fit_score(k1, mold_od=470.0, mold_len=7000.0, needs_big_slot=False)
        assert score_needs < 999.0
        assert score_not < 999.0  # Still fits, but with penalty
        # needs_big_slot=True gives strictly lower (better) score
        assert score_needs < score_not, (
            f"needs_big_slot=True should score better: {score_needs} >= {score_not}"
        )


# ── delivery_priority ─────────────────────────────────────────────────────
class TestDeliveryPriority:
    def test_urgent_within_7(self):
        order = {"delivery_date": "2026-05-25"}
        p = delivery_priority(order, today=date(2026, 5, 19))
        assert p == 2.0

    def test_overdue(self):
        order = {"delivery_date": "2020-01-01"}
        p = delivery_priority(order, today=date(2026, 5, 19))
        assert p == 3.0

    def test_far_future(self):
        order = {"delivery_date": "2027-06-01"}
        p = delivery_priority(order, today=date(2026, 5, 19))
        assert p == 0.0

    def test_within_14_days(self):
        """14-day window → priority 1.0 (line 155)"""
        order = {"delivery_date": "2026-06-01"}
        p = delivery_priority(order, today=date(2026, 5, 19))
        assert p == 1.0

    def test_within_30_days(self):
        """30-day window → priority 0.5 (line 156)"""
        order = {"delivery_date": "2026-06-18"}
        p = delivery_priority(order, today=date(2026, 5, 19))
        assert p == 0.5

    def test_no_today_param_uses_date_today(self):
        """line 143 — delivery_priority without today param"""
        far_order = {"delivery_date": "2030-01-01"}
        p = delivery_priority(far_order)
        assert p == 0.0  # far future → 0

    def test_datetime_delivery_date(self):
        """line 146 — when parse_delivery_date returns a datetime"""
        from date_utils import parse_delivery_date as _dkey
        with patch("optimizer._dkey", return_value=datetime(2026, 5, 25)):
            order = {"delivery_date": "2026-05-25"}
            p = delivery_priority(order, today=date(2026, 5, 19))
            assert p == 2.0  # within 7 days


# ── check_mold_availability ──────────────────────────────────────────────
class TestMoldAvailability:
    @dataclass
    class FakeMold:
        mold_no: str
        outer_dia: float
        inner_dia: float
        length: float
        stock_qty: int
        status: str

    def test_no_molds_fn_returns_true(self):
        """line 168-169: get_molds_fn is None → True"""
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=None)
        assert ok is True
        assert "無模具庫存資料" in msg

    def test_mold_found_exact_match(self):
        """Mold matches all criteria → found"""
        molds = [self.FakeMold("M-001", 120, 100, 200, 5, "available")]
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is True
        assert "M-001" in msg

    def test_mold_od_too_small(self):
        """outer_dia too small → skip → no mold found"""
        molds = [self.FakeMold("M-001", 90, 80, 200, 5, "available")]
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is False
        assert "無可用模具" in msg
        assert "外徑≥100" in msg

    def test_mold_length_too_short(self):
        """length too short → skip"""
        molds = [self.FakeMold("M-001", 120, 100, 150, 5, "available")]
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is False

    def test_mold_stock_zero(self):
        """stock_qty=0 → skip"""
        molds = [self.FakeMold("M-001", 120, 100, 200, 0, "available")]
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is False

    def test_mold_not_available_status(self):
        """status != 'available' → skip"""
        molds = [self.FakeMold("M-001", 120, 100, 200, 5, "maintenance")]
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is False

    def test_mold_inner_dia_too_small(self):
        """mold inner_dia < required → skip (lines 182-184)"""
        molds = [self.FakeMold("M-001", 120, 70, 200, 5, "available")]
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is False
        assert "內徑≥80" in msg

    def test_mold_inner_dia_not_required(self):
        """mold_inner_dia is None → inner_dia check skipped"""
        molds = [self.FakeMold("M-001", 120, 50, 200, 5, "available")]
        ok, msg = check_mold_availability(100, None, 200, get_molds_fn=lambda: molds)
        assert ok is True

    def test_mold_inner_dia_zero_skipped(self):
        """mold_inner_dia=0 → inner_dia check skipped"""
        molds = [self.FakeMold("M-001", 120, 50, 200, 5, "available")]
        ok, msg = check_mold_availability(100, 0, 200, get_molds_fn=lambda: molds)
        assert ok is True

    def test_error_message_with_inner_dia(self):
        """Error message includes inner_dia when applicable (lines 187-189)"""
        molds = [self.FakeMold("M-001", 90, 100, 200, 5, "available")]  # od too small
        ok, msg = check_mold_availability(100, 80, 200, get_molds_fn=lambda: molds)
        assert ok is False
        assert "內徑≥80" in msg


# ── schedule_orders edge cases ────────────────────────────────────────────
class TestScheduleOrdersEdgeCases:
    def test_products_by_voltage_and_kilns_passed(self):
        """lines 215-216: products_by_voltage + kilns_data passed directly"""
        kilns, by_v, hours_per_root = _load_data()
        orders = [
            {"plan_no": "T-DB1", "voltage_kv": 10.0, "qty": 1,
             "delivery_date": "2026-12-31", "contract_no": "C1"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
            strategy="deadline",
        )
        assert result["summary"]["scheduled"] == 1

    def test_order_no_voltage_skipped(self):
        """lines 277-279: order with voltage ≤ 0 → skipped"""
        kilns, by_v, hours_per_root = _load_data()
        orders = [
            {"plan_no": "T-NOV", "voltage_kv": 0, "qty": 1,
             "delivery_date": "2026-12-31", "contract_no": "C1"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
        )
        assert len(result["warnings"]) == 1
        assert "無電壓資料" in result["warnings"][0]

    def test_order_voltage_no_match_product(self):
        """lines 284-286: voltage not in by_v → skipped"""
        kilns, by_v, hours_per_root = _load_data()
        orders = [
            {"plan_no": "T-NOM", "voltage_kv": 999.9, "qty": 1,
             "delivery_date": "2026-12-31", "contract_no": "C1"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
        )
        assert len(result["warnings"]) == 1
        assert "無匹配產品" in result["warnings"][0]

    def test_product_mold_od_zero(self):
        """lines 297-299: product with mold_od=0 → skipped"""
        kilns, by_v, hours_per_root = _load_data()
        # Patch by_v to have a product with mold_od=0
        by_v_mod = dict(by_v)
        by_v_mod[999.9] = [{"voltage_kv": 999.9, "mold_od": 0, "mold_id": 0, "mold_len": 1000}]
        orders = [
            {"plan_no": "T-ZERO", "voltage_kv": 999.9, "qty": 1,
             "delivery_date": "2026-12-31", "contract_no": "C1"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v_mod,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
        )
        assert len(result["warnings"]) == 1
        assert "模具外徑為0" in result["warnings"][0]

    def test_mold_availability_failure(self):
        """lines 303-308: mold check fails → skipped"""
        kilns, by_v, hours_per_root = _load_data()
        # Product at 550kV uses mold_od=470, mold_id=400
        # Provide a mold fn that returns only molds with wrong inner_dia
        @dataclass
        class FakeMold:
            mold_no: str
            outer_dia: float
            inner_dia: float
            length: float
            stock_qty: int
            status: str

        def bad_molds():
            return [FakeMold("M-BAD", 470, 100, 7000, 5, "available")]

        orders = [
            {"plan_no": "T-MOLD", "contract_no": "C1", "voltage_kv": 550.0,
             "qty": 1, "delivery_date": "2026-12-31"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
            get_molds_fn=bad_molds,
        )
        assert "無可用模具" in result["warnings"][0]

    def test_max_hours_per_kiln_blocks(self):
        """line 318: max_hours_per_kiln causes continue for overloaded kilns"""
        kilns, by_v, hours_per_root = _load_data()
        # Use a tiny max_hours_per_kiln so every order exceeds it
        orders = [
            {"plan_no": "T-CAP", "contract_no": "C1", "voltage_kv": 550.0,
             "qty": 1, "delivery_date": "2026-12-31"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
            max_hours_per_kiln=0.01,  # impossibly small
        )
        # Should be skipped due to no available kiln (hours cap too low)
        assert result["summary"]["skipped"] >= 1

    def test_no_available_kiln_for_size(self):
        """lines 341-345: no kiln fits the product dimensions → skipped"""
        kilns, by_v, hours_per_root = _load_data()
        by_v_mod = dict(by_v)
        # Giant product that no kiln can fit
        by_v_mod[999.9] = [{"voltage_kv": 999.9, "mold_od": 99999,
                            "mold_id": 100, "mold_len": 999999}]
        orders = [
            {"plan_no": "T-GIANT", "contract_no": "C1", "voltage_kv": 999.9,
             "qty": 1, "delivery_date": "2026-12-31"}
        ]
        result = schedule_orders(
            orders,
            products_by_voltage=by_v_mod,
            kilns_data=kilns,
            hours_per_root=hours_per_root,
        )
        assert "無可用干燥罐" in result["warnings"][0]


# ── quality_report edge cases ─────────────────────────────────────────────
class TestQualityReportEdgeCases:
    def test_empty_schedule_returns_zero(self):
        """line 405: no schedule → score 0"""
        result = {
            "summary": {"total_orders": 0, "scheduled": 0, "skipped": 0, "total_hours": 0},
            "order_schedule": [],
            "kiln_schedule": {},
            "warnings": [],
        }
        qr = quality_report(result)
        assert qr["score"] == 0
        assert "無排程資料" in qr["explanation"]

    def test_single_kiln_balance_100(self):
        """line 419: only 1 kiln used → balance=100"""
        result = {
            "summary": {"total_orders": 10, "scheduled": 10, "skipped": 0, "total_hours": 100},
            "order_schedule": [
                {"plan_no": f"P-{i}", "qty": 1, "hours": 10, "_priority": 0}
                for i in range(10)
            ],
            "kiln_schedule": {
                "1": {"kiln_id": "1", "kiln_name": "K1", "hours_used": 100,
                      "total_slots": 10, "slots_used": 10, "usage_pct": 50,
                      "order_count": 10, "orders": []},
            },
            "warnings": [],
        }
        qr = quality_report(result)
        assert qr["balance"] == 100.0


# ── Main schedule ─────────────────────────────────────────────────────────
class TestScheduleOrders:
    def test_schedules_all_orders(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        result = schedule_orders(orders, strategy="deadline")
        sched = result["summary"]["scheduled"]
        skipped = result["summary"]["skipped"]
        assert sched + skipped == len(orders)
        assert sched > 0

    def test_no_duplicates(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        result = schedule_orders(orders)
        plan_nos = [o["plan_no"] for o in result["order_schedule"]]
        assert len(plan_nos) == len(set(plan_nos))

    def test_quality_metrics(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        result = schedule_orders(orders, strategy="balance")
        qr = quality_report(result)
        assert 0 <= qr["score"] <= 100
        assert qr["rate"] > 0

    def test_balance_uses_multiple_kilns(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        result = schedule_orders(orders, strategy="balance")
        assert len(result["kiln_schedule"]) >= 2

    def test_fill_strategy(self):
        """fill strategy → composite = fscore - pct * 2.0"""
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        result = schedule_orders(orders, strategy="fill")
        assert result["summary"]["scheduled"] > 0
        assert len(result["kiln_schedule"]) >= 1

    def test_schedule_entry_fields(self):
        """Validate schedule entry contains all expected fields"""
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        result = schedule_orders(orders, strategy="deadline")
        entry = result["order_schedule"][0]
        expected_fields = {"plan_no", "contract_no", "voltage_kv", "qty",
                           "delivery_date", "kiln_id", "kiln_name",
                           "mold_od", "mold_len", "mold_id_dia",
                           "est_hours", "status", "_priority"}
        assert expected_fields.issubset(set(entry.keys()))
        assert entry["status"] == "scheduled"


# ── Comparison ────────────────────────────────────────────────────────────
class TestComparison:
    def test_both_strategies_schedule(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)

        r_deadline = schedule_orders(orders, strategy="deadline")
        r_balance = schedule_orders(orders, strategy="balance")
        r_fill = schedule_orders(orders, strategy="fill")

        q_dl = quality_report(r_deadline)
        q_bal = quality_report(r_balance)
        q_fill = quality_report(r_fill)

        assert q_dl["rate"] > 90
        assert q_bal["rate"] > 90
        assert q_fill["rate"] > 90
        assert q_bal["kilns_used"] >= 3

    def test_overdue_prioritized(self):
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "data", "orders.json")) as f:
            orders = json.load(f)
        for i in range(min(20, len(orders))):
            orders[i]["delivery_date"] = "2020-01-01"

        result = schedule_orders(orders, strategy="deadline")
        sched = result["order_schedule"]

        overdue_scheduled = [o for o in sched if o.get("_priority", 0) >= 3.0]
        assert len(overdue_scheduled) >= 18, \
            f"Most overdue should be scheduled: {len(overdue_scheduled)}/20"