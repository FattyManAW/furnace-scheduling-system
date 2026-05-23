"""Test: reroute_on_congestion hook — before/after WIP 對比

使用 furnace-scheduling-system 真實 DB + optimizer 數據
驗證：congestion detect → redirect → before/after report
"""
from __future__ import annotations

import json
import sys
import os

# Ensure backend is importable
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, backend_dir)

from database import SessionLocal, Base, engine
from seed_data import seed_all
from engine.data_layer import load_all_optimizer_data
from engine.optimizer import schedule_orders, quality_report
from engine.reroute import reroute_on_congestion, reroute_report

Base.metadata.create_all(bind=engine)

def test_reroute_before_after():
    """Full integration: seed → schedule → detect → reroute → report"""
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
        moved = rr.get("moved", 0)
        total_orders = sum(k.get("order_count", 0) for k in rerouted["kiln_schedule"].values())
        expected = result["summary"]["scheduled"]
        assert total_orders == expected, f"Order count mismatch: {total_orders} vs {expected}"

        return rerouted

    finally:
        db.close()


if __name__ == "__main__":
    result = test_reroute_before_after()
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