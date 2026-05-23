"""
oven_scheduler/optimizer.py  v2
Best-fit furnace scheduler — improved multi-pass filling.
"""
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from data_loader import load_all

# shared date utils (same module as backend/date_utils, imported at runtime)
_DPATH = __import__('backend.date_utils', fromlist=['excel_to_date'])
excel_to_date = _DPATH.excel_to_date


def _load():
    d = load_all()
    return d["products"], d["dryers"], d["mold_inventory"], d["orders"]


_PRODUCTS = None
_DRYERS = None
_MOLDS = None
_ORDERS = None


def _init():
    global _PRODUCTS, _DRYERS, _MOLDS, _ORDERS
    if _PRODUCTS is None:
        _PRODUCTS, _DRYERS, _MOLDS, _ORDERS = _load()


def get_mold_for_product(voltage_kv, current_a):
    _init()
    key = (float(voltage_kv), float(current_a))
    if key in _PRODUCTS:
        p = _PRODUCTS[key]
        return (round(p["mold_od"], 1), round(p["mold_id"], 1), round(p["mold_length"], 1))
    # closest voltage fallback
    best = None
    best_dist = 999
    for (v, _a), p in _PRODUCTS.items():
        d = abs(v - voltage_kv)
        if d < best_dist:
            best_dist = d
            best = (round(p["mold_od"], 1), round(p["mold_id"], 1), round(p["mold_length"], 1))
    return best


def _mold_fits_plan(ms, upper, lower):
    """Return True if mold matches upper or lower zone."""
    mod, mid, mlen = ms
    for z in (upper, lower):
        if z["qty"] > 0 and abs(z["od"] - mod) < 1 and abs(z["id"] - mid) < 1 and abs(z["length"] - mlen) < 50:
            return True
    return False


def _plan_capacity(ms, plan):
    """Total molds this plan can hold for the given mold spec."""
    if _mold_fits_plan(ms, plan["upper"], plan["lower"]):
        return plan["upper"]["qty"] + plan["lower"]["qty"]
    return 0


def _total_inv(ms):
    """Total available inventory for this mold spec."""
    return sum(m["qty"] for m in _MOLDS
               if (round(m["od"], 1), round(m["id_inner"], 1), round(m["length"], 1)) == ms)


def schedule(orders=None, selected_furnaces=None):
    """
    Multi-pass greedy scheduler:
      1. Group orders by mold spec
      2. Sort groups by earliest delivery date
      3. For each group, repeatedly fill all available furnaces (best-fit first)
         until inventory is exhausted
    """
    _init()
    if orders is None:
        orders = list(_ORDERS)

    furnaces = _DRYERS
    if selected_furnaces:
        furnaces = [f for f in _DRYERS if f["name"] in selected_furnaces]

    orders = sorted(orders, key=lambda o: (o.get("delivery_date", ""), -o.get("qty", 0)))

    # ── anchor date: earliest real delivery date, used for calendar day output ──
    anchor = datetime.now()
    for o in orders:
        raw = o.get("delivery_date", "")
        try:
            d = excel_to_date(raw)
            parsed = datetime.strptime(d, "%Y-%m-%d")
            if parsed < anchor:
                anchor = parsed
        except Exception:
            continue
    anchor = anchor.replace(hour=0, minute=0, second=0, microsecond=0)

    # Group by mold spec
    order_groups = defaultdict(list)
    for o in orders:
        ms = get_mold_for_product(o["voltage_kv"], o["current_a"])
        if ms:
            order_groups[ms].append(o)

    # Sort groups by earliest delivery date
    sorted_groups = []
    for ms, gos in order_groups.items():
        earliest = min(go.get("delivery_date", "") for go in gos)
        sorted_groups.append((earliest, ms, gos))
    sorted_groups.sort(key=lambda x: x[0])

    batches = []
    furnace_day = {f["name"]: 0 for f in furnaces}  # next available day per furnace
    assigned_orders = {}  # order_id -> remaining qty

    for _earliest, ms, gos in sorted_groups:
        remaining = sum(o["qty"] for o in gos)
        available = _total_inv(ms)

        while remaining > 0 and available > 0:
            # Score all furnace+plan combos: ( -furnace_day, capacity desc )
            candidates = []
            for f in furnaces:
                fd = furnace_day[f["name"]]
                for pi, plan in enumerate(f.get("plans", [])):
                    cap = _plan_capacity(ms, plan)
                    if cap > 0:
                        candidates.append((fd, -cap, f["name"], f, pi, plan))

            if not candidates:
                break  # no furnace can hold this mold

            candidates.sort()  # earliest furnace first, then largest capacity
            fd, _neg_cap, fname, furnace, pi, plan = candidates[0]

            batch_qty = min(-candidates[0][1], remaining, available)
            if batch_qty <= 0:
                break

            # Assign orders (greedy by earliest delivery first)
            assigned = []
            qty_left = batch_qty
            for o in gos:
                if qty_left <= 0:
                    break
                remaining_o = assigned_orders.get(o["order_id"], o["qty"])
                take = min(remaining_o, qty_left)
                if take > 0:
                    assigned.append({
                        "order_id": o["order_id"],
                        "qty": take,
                        "voltage_kv": o["voltage_kv"],
                        "current_a": o["current_a"],
                    })
                    assigned_orders[o["order_id"]] = remaining_o - take
                    qty_left -= take
                    remaining -= take

            available -= batch_qty
            start_day = furnace_day[fname]
            end_day = start_day + 1

            batches.append({
                "batch_id": f"B{len(batches)+1:03d}",
                "furnace": fname,
                "furnace_spec": f"Φ{furnace['inner_d']}×{furnace['height']}mm",
                "plan": plan["plan"],
                "mold_spec": {"od": ms[0], "id": ms[1], "length": ms[2]},
                "molds": assigned,
                "total_molds": batch_qty,
                "start_day": start_day,
                "end_day": end_day,
                "start_date": (anchor + timedelta(days=start_day)).strftime("%Y-%m-%d"),
                "end_date": (anchor + timedelta(days=end_day)).strftime("%Y-%m-%d"),
            })
            furnace_day[fname] = end_day + 1

    return {
        "batches": batches,
        "total_batches": len(batches),
        "total_orders": len(orders),
        "furnace_count": len(furnaces),
        "furnace_day": furnace_day,
        "total_days": max(furnace_day.values()) if furnace_day else 0,
    }


def get_data_summary():
    _init()
    return {
        "products": {f"{k[0]}kV/{k[1]}A": v for k, v in _PRODUCTS.items()},
        "dryers": [{"name": d["name"], "inner_d": d["inner_d"], "height": d["height"], "plans": len(d["plans"])} for d in _DRYERS],
        "molds": [{"od": m["od"], "id": m["id_inner"], "length": m["length"], "qty": m["qty"]} for m in _MOLDS],
        "orders_count": len(_ORDERS),
    }


if __name__ == "__main__":
    r = schedule()
    print(f"Batches: {r['total_batches']}, Days: {r['total_days']}")
    total_m = sum(b['total_molds'] for b in r['batches'])
    print(f"Total molds scheduled: {total_m}")
    for b in r['batches'][:10]:
        ms = b['mold_spec']
        print(f"  {b['batch_id']}: {b['furnace']} plan={b['plan']} {b['total_molds']}x {ms['od']}×{ms['id']}×{ms['length']}")
