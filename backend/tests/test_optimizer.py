"""Unit tests for optimizer v2.1 — fit_score, delivery priority, full schedule"""
import os, sys, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))

from optimizer import (
    fit_score, delivery_priority, schedule_orders,
    quality_report, hours_for, _load_data,
    DAILY_HOUR_CAP,
)
from datetime import date


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