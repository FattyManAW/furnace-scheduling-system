from __future__ import annotations

"""
oven_scheduler/engine.py
Database-backed scheduling engine.
Reads from DB, writes Batch records back to DB.
"""
import json
from collections import defaultdict

from sqlalchemy.orm import Session

from database import Batch, Dryer, DryerPlan, MoldType, Order, ProductSpec


def _plan_capacity(ms, plan: DryerPlan):
    """Check if mold spec matches plan; return total capacity if yes, else 0."""
    mod, mid, mlen = ms
    if plan.upper_qty > 0 and abs(plan.upper_od - mod) < 1 and abs(plan.upper_id - mid) < 1 and abs(plan.upper_length - mlen) < 50:
        return plan.upper_qty + plan.lower_qty
    if plan.lower_qty > 0 and abs(plan.lower_od - mod) < 1 and abs(plan.lower_id - mid) < 1 and abs(plan.lower_length - mlen) < 50:
        return plan.upper_qty + plan.lower_qty
    return 0


def _total_inv(ms, molds: list[MoldType]):
    return sum(m.quantity for m in molds
               if (round(m.outer_diameter, 1), round(m.inner_diameter, 1), round(m.length, 1)) == ms)


def run_schedule(session: Session, order_ids: list[str] | None = None) -> dict:
    """Run scheduling and persist batches to DB."""
    # Load data
    dryers = session.query(Dryer).all()
    mold_types = session.query(MoldType).all()
    products = session.query(ProductSpec).all()
    query = session.query(Order)
    if order_ids:
        query = query.filter(Order.order_id.in_(order_ids))
    orders = query.order_by(Order.delivery_date.asc(), Order.quantity.desc()).all()

    # Build product lookup
    prod_map = {}
    for p in products:
        prod_map[(p.voltage_kv, p.current_a)] = (p.mold_od, p.mold_id, p.mold_length)

    # Group orders by mold spec
    order_groups = defaultdict(list)
    for o in orders:
        kv, amp = o.voltage_kv, o.current_a
        if (kv, amp) in prod_map:
            ms = prod_map[(kv, amp)]
            order_groups[ms].append(o)

    # Sort groups by earliest delivery date
    sorted_groups = []
    for ms, gos in order_groups.items():
        earliest = min(go.delivery_date for go in gos)
        sorted_groups.append((earliest, ms, gos))
    sorted_groups.sort(key=lambda x: x[0])

    # Dryer plans pre-load
    dryer_plans = {}
    for d in dryers:
        dryer_plans[d.name] = list(d.plans)

    # Clean old batches for these orders
    session.query(Batch).delete()

    batches = []
    furnace_day = {d.name: 0 for d in dryers}
    assigned_orders = {}

    for _earliest, ms, gos in sorted_groups:
        remaining = sum(o.quantity for o in gos)
        available = _total_inv(ms, mold_types)

        while remaining > 0 and available > 0:
            candidates = []
            for f in dryers:
                fd = furnace_day[f.name]
                for plan in dryer_plans[f.name]:
                    cap = _plan_capacity(ms, plan)
                    if cap > 0:
                        candidates.append((fd, -cap, f.name, f, plan))

            if not candidates:
                break
            candidates.sort()
            fd, _neg_cap, fname, furnace, plan = candidates[0]
            batch_qty = min(-candidates[0][1], remaining, available)
            if batch_qty <= 0:
                break

            # Assign orders
            assigned = []
            qty_left = batch_qty
            for o in gos:
                if qty_left <= 0:
                    break
                remaining_o = assigned_orders.get(o.order_id, o.quantity)
                take = min(remaining_o, qty_left)
                if take > 0:
                    assigned.append({
                        "order_id": o.order_id,
                        "qty": take,
                        "voltage_kv": o.voltage_kv,
                        "current_a": o.current_a,
                    })
                    assigned_orders[o.order_id] = remaining_o - take
                    qty_left -= take
                    remaining -= take

            available -= batch_qty
            start_day = furnace_day[fname]
            end_day = start_day + 1

            batch = Batch(
                batch_id=f"B{len(batches)+1:03d}",
                dryer_name=fname,
                dryer_spec=f"Φ{furnace.inner_diameter:.0f}×{furnace.height:.0f}mm",
                plan_label=plan.plan_label,
                mold_od=ms[0],
                mold_id=ms[1],
                mold_length=ms[2],
                total_molds=batch_qty,
                start_day=start_day,
                end_day=end_day,
                start_date=f"Day {start_day}",
                end_date=f"Day {end_day}",
                orders_json=json.dumps(assigned),
            )
            session.add(batch)
            batches.append(batch)
            furnace_day[fname] = end_day + 1

    session.commit()
    return _serialize(batches, dryers, furnace_day)


def _serialize(batches, dryers, furnace_day):
    result = {"batches": [], "furnace_day": furnace_day}
    for b in batches:
        orders_data = json.loads(b.orders_json) if b.orders_json else []
        result["batches"].append({
            "batch_id": b.batch_id,
            "furnace": b.dryer_name,
            "furnace_spec": b.dryer_spec,
            "plan": b.plan_label,
            "mold_spec": {"od": b.mold_od, "id": b.mold_id, "length": b.mold_length},
            "molds": orders_data,
            "total_molds": b.total_molds,
            "start_day": b.start_day,
            "end_day": b.end_day,
            "start_date": b.start_date,
            "end_date": b.end_date,
        })
    dryers_used = list(set(b.dryer_name for b in batches))
    result["total_batches"] = len(batches)
    result["furnace_count"] = len(dryers)
    result["furnace_used_count"] = len(dryers_used)
    result["total_days"] = max(furnace_day.values()) if furnace_day else 0
    result["dryers_used"] = dryers_used
    return result
