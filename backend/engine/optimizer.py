"""排程優化引擎 v2.1 — 基於 fit_score 的多目標優化"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta
from typing import Callable

DAILY_HOUR_CAP = 1098.0


# ── helpers ──────────────────────────────────────────────────────────────
def _sf(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    if s in ("", "－", "-", "—"):
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def _si(v):
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).strip().replace(",", "")
    if s in ("", "－", "-", "—"):
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def _dkey(o):
    """Parse delivery_date to date object with Excel serial date support."""
    d = o.get("delivery_date", "")
    if isinstance(d, (int, float)):
        if d > 10000:
            return (datetime(1899, 12, 30) + timedelta(days=int(d))).date()
        return date.today() + timedelta(days=60)
    s = str(d).strip()
    if not s:
        return date.today() + timedelta(days=60)
    # Excel serial date string "46117.0"
    try:
        serial = float(s)
        if serial > 10000:
            return (datetime(1899, 12, 30) + timedelta(days=int(serial))).date()
    except (ValueError, OverflowError):
        pass
    # Standard date formats
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except Exception:
            continue
    return date.today() + timedelta(days=60)


def _load_data(data_dir: str | None = None):
    if data_dir is None:
        # Try Docker layout (backend/data/) then repo root (../../data/)
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"),
        ]
        for d in candidates:
            if os.path.isfile(os.path.join(d, "kilns.json")):
                data_dir = d
                break
        if data_dir is None:
            data_dir = candidates[0]
    with open(os.path.join(data_dir, "kilns.json")) as f:
        kilns = json.load(f)
    with open(os.path.join(data_dir, "products.json")) as f:
        products = json.load(f)
    with open(os.path.join(data_dir, "processes.json")) as f:
        processes = json.load(f)

    by_v: dict[float, list[dict]] = {}
    for p in products:
        v = round(float(p.get("voltage_kv", 0)), 1)
        if v > 0:
            by_v.setdefault(v, []).append(p)

    h10 = sum(float(r.get("h10", 0) or 0) for r in processes)
    h24 = sum(float(r.get("h24", 0) or 0) for r in processes)
    h36 = sum(float(r.get("h36", 0) or 0) for r in processes)
    h40 = sum(float(r.get("h40", 0) or 0) for r in processes)
    hours_per_root: dict[int, float] = {10: h10, 24: h24, 36: h36, 40: h40}

    return kilns, by_v, hours_per_root


def hours_for(qty, voltage_kv, hours_per_root: dict | None = None):
    if hours_per_root is None:
        _, _, hours_per_root = _load_data()
    v = round(float(voltage_kv), 1)
    if v <= 15:
        h = float(hours_per_root.get(10, 0))
    elif v <= 30:
        h = float(hours_per_root.get(24, 0))
    elif v <= 38:
        h = float(hours_per_root.get(36, 0))
    else:
        h = float(hours_per_root.get(40, hours_per_root.get(36, 0)))
    return round(h * qty, 1)


# ── fit_score (fixed and now ACTUALLY USED) ──────────────────────────────
def fit_score(kiln: dict, mold_od: float, mold_len: float,
              mold_inner_dia: float = 0.0, needs_big_slot: bool = False) -> float:
    """
    Lower score = better fit (negative = waste is less than the slot).
    Now also considers:
    - inner_dia match (prefer tight fit)
    - big slot penalty (don't waste large slots on small products)
    """
    best = 999.0
    for _sname, scheme in kiln.get("schemes", {}).items():
        for pos in ("upper", "lower"):
            slot = scheme[pos]
            sod = _sf(slot.get("od", 0))
            sid = _sf(slot.get("id", 0))
            slen = _sf(slot.get("len", 0))
            if sod < mold_od or slen < mold_len:
                continue

            # waste ratio: lower is better
            od_waste = (sod - mold_od) / max(sod, 1)
            len_waste = (slen - mold_len) / max(slen, 1)

            # inner-dia: prefer close fit (within 30mm)
            id_bonus = 0.0
            if mold_inner_dia > 0 and sid > mold_inner_dia:
                id_bonus = (sid - mold_inner_dia) / max(sid, 1) * 2.0

            # big slot penalty: small products shouldn't waste large slots
            big_penalty = 0.0
            if needs_big_slot and sod >= 470:
                big_penalty = 0.0  # needs big slot, no penalty
            elif not needs_big_slot and sod >= 470:
                big_penalty = 1.0  # waste of big slot

            score = od_waste * 0.4 + len_waste * 0.3 + id_bonus + big_penalty
            if score < best:
                best = score

    return best


def delivery_priority(order: dict, today: date | None = None) -> float:
    """
    Calculate delivery priority weight. Higher = more urgent.
    - Overdue: weight +3.0 (very high priority)
    - Due within 7 days: +2.0
    - Due within 14 days: +1.0
    - Due within 30 days: +0.5
    - Later: base 0.0
    """
    if today is None:
        today = date.today()
    due = _dkey(order)
    if isinstance(due, datetime):
        due = due.date()
    diff = (due - today).days

    if diff < 0:
        return 3.0
    elif diff <= 7:
        return 2.0
    elif diff <= 14:
        return 1.0
    elif diff <= 30:
        return 0.5
    else:
        return 0.0


def check_mold_availability(mold_od: float, mold_inner_dia: float | None,
                            mold_len: float, get_molds_fn: Callable[[], list] | None = None
                            ) -> tuple[bool, str]:
    """
    Check if required mold is available in inventory.
    Returns (available, message).
    """
    if get_molds_fn is None:
        return True, "無模具庫存資料"

    molds = get_molds_fn()
    for m in molds:
        mod = getattr(m, "outer_dia", 0)
        getattr(m, "inner_dia", 0)
        mlen = getattr(m, "length", 0)
        stock = getattr(m, "stock_qty", 0)
        status = getattr(m, "status", "available")
        if (mod >= mold_od and mlen >= mold_len and stock > 0
                and status == "available"):
            return True, f"可用模具: {getattr(m, 'mold_no', '?')}"
    return False, f"無可用模具 (外徑≥{mold_od}, 長度≥{mold_len})"


# ── main scheduler (REWRITTEN) ───────────────────────────────────────────
def schedule_orders(
    orders: list[dict],
    data_dir: str | None = None,
    get_molds_fn: Callable[[], list] | None = None,
    strategy: str = "deadline",
    max_hours_per_kiln: float | None = None,
    products_by_voltage: dict | None = None,
    kilns_data: dict | None = None,
    hours_per_root: dict | None = None,
) -> dict:
    """
    Enhanced scheduling with:
    - fit_score-based kiln selection
    - delivery-date priority weighting
    - mold availability check (via get_molds_fn)
    - kiln capacity limits

    strategy: "deadline" / "balance" / "fill"
    """
    # ── 資料來源：優先使用傳入參數（來自 DB data_layer），fallback 讀 JSON ──
    if products_by_voltage is not None and kilns_data is not None and hours_per_root is not None:
        by_v = products_by_voltage
        kilns = kilns_data
    else:
        kilns, by_v, hours_per_root = _load_data(data_dir)
    today = date.today()

    # ── priority calculation ───────────────────────────────────────
    for o in orders:
        o["_priority"] = delivery_priority(o, today)

    # Sort: highest priority first, then earliest delivery
    orders_sorted = sorted(orders, key=lambda o: (-o["_priority"], _dkey(o)))

    # ── kiln state tracking ─────────────────────────────────────────
    # Per-kiln hours limit: only enforced when max_hours_per_kiln is set.
    # Global limit: total slots per kiln (not hours).
    furnace_state = {}
    for kid, kiln in kilns.items():
        total_slots = 0
        for _sname, scheme in kiln.get("schemes", {}).items():
            for pos in ("upper", "lower"):
                total_slots += _si(scheme[pos].get("qty", 0))
        max_sod = 0.0
        max_slen = 0.0
        for _sname, scheme in kiln.get("schemes", {}).items():
            for pos in ("upper", "lower"):
                max_sod = max(max_sod, _sf(scheme[pos].get("od", 0)))
                max_slen = max(max_slen, _sf(scheme[pos].get("len", 0)))

        furnace_state[kid] = {
            "name": kiln.get("name", ""),
            "inner_dia": kiln.get("inner_dia", 0),
            "height": kiln.get("height", 0),
            "total_slots": total_slots,
            "slots_used": 0,
            "hours_used": 0.0,
            "max_od": max_sod,
            "max_len": max_slen,
            "schemes": list(kiln.get("schemes", {}).keys()),
        }

    sum(s["total_slots"] for s in furnace_state.values())
    global_hour_cap = DAILY_HOUR_CAP * 28  # 28 kilns × daily cap

    total_hours_used = 0.0
    result: dict = {
        "summary": {
            "total_orders": len(orders_sorted),
            "scheduled": 0,
            "skipped": 0,
            "total_hours": 0.0,
            "daily_cap": DAILY_HOUR_CAP,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
        "order_schedule": [],
        "kiln_schedule": {},
        "warnings": [],
    }

    for order in orders_sorted:
        po = str(order.get("plan_no", ""))
        voltage = _sf(order.get("voltage_kv", 0))
        if voltage <= 0:
            result["warnings"].append(f"{po}: 無電壓資料")
            result["summary"]["skipped"] += 1
            continue

        v_key = round(voltage, 1)
        prods = by_v.get(v_key, [])
        if not prods:
            result["warnings"].append(f"{po}: 電壓 {voltage}kV 無匹配產品")
            result["summary"]["skipped"] += 1
            continue

        prod = prods[0]
        qty = _si(order.get("qty", 0))
        delivery = str(_dkey(order))
        contract = str(order.get("contract_no", ""))

        mold_od = _sf(prod.get("mold_od", 0))
        mold_len = _sf(prod.get("mold_len", 0))
        mold_inner_dia = _sf(prod.get("mold_id", 0))  # "mold_id" in JSON = inner_dia
        if mold_od == 0:
            result["warnings"].append(f"{po}: 產品模具外徑為0")
            result["summary"]["skipped"] += 1
            continue

        # ── mold availability check ──────────────────────────────
        if get_molds_fn:
            avail, msg = check_mold_availability(mold_od, mold_inner_dia,
                                                 mold_len, get_molds_fn)
            if not avail:
                result["warnings"].append(f"{po}: {msg}")
                result["summary"]["skipped"] += 1
                continue

        needs_big = mold_od >= 470

        # ── kiln selection with fit_score ─────────────────────────
        candidates = []
        for kid, state in furnace_state.items():
            if state["slots_used"] >= state["total_slots"]:
                continue
            if max_hours_per_kiln and state["hours_used"] + hours_for(qty, voltage, hours_per_root) > max_hours_per_kiln:
                continue

            # Must fit in kiln
            if mold_od > state["max_od"] or mold_len > state["max_len"]:
                continue

            # Use fit_score!
            fscore = fit_score(kilns[kid], mold_od, mold_len,
                              mold_inner_dia, needs_big)

            # Composite score: fit quality + load balance
            avg_h_per_kiln = max(global_hour_cap / 28, 1)
            pct = state["hours_used"] / avg_h_per_kiln
            if strategy == "balance":
                composite = fscore + pct * 2.0  # prefer less-loaded kilns
            elif strategy == "fill":
                composite = fscore - pct * 2.0  # prefer more-loaded (fill up)
            else:  # deadline/default: pure fit
                composite = fscore

            candidates.append((composite, kid))

        if not candidates:
            result["warnings"].append(
                f"{po}: 無可用干燥罐 (od={mold_od}, len={mold_len})"
            )
            result["summary"]["skipped"] += 1
            continue

        # Pick best candidate (lowest score)
        candidates.sort(key=lambda x: x[0])
        best = candidates[0][1]

        h = hours_for(qty, voltage, hours_per_root)
        furnace_state[best]["slots_used"] += 1
        furnace_state[best]["hours_used"] += h
        total_hours_used += h

        result["order_schedule"].append({
            "plan_no": po,
            "contract_no": contract,
            "voltage_kv": voltage,
            "qty": qty,
            "delivery_date": delivery,
            "kiln_id": best,
            "kiln_name": furnace_state[best]["name"],
            "mold_od": mold_od,
            "mold_len": mold_len,
            "mold_id_dia": prod.get("mold_id", 0),
            "est_hours": h,
            "status": "scheduled",
            "_priority": order.get("_priority", 0),
        })

    result["summary"]["scheduled"] = len(result["order_schedule"])
    result["summary"]["total_hours"] = round(total_hours_used, 1)

    # Build kiln summary
    for kid, state in furnace_state.items():
        if state["slots_used"] > 0:
            pct = round(state["hours_used"] / max(global_hour_cap / 28, 1) * 100, 1)
            orders_in = [o for o in result["order_schedule"] if o["kiln_id"] == kid]
            result["kiln_schedule"][kid] = {
                "kiln_id": kid,
                "kiln_name": state["name"],
                "total_slots": state["total_slots"],
                "slots_used": state["slots_used"],
                "hours_used": round(state["hours_used"], 1),
                "usage_pct": min(round(pct, 1), 100),
                "order_count": len(orders_in),
                "orders": [
                    {"plan_no": o["plan_no"], "qty": o["qty"], "hours": o["est_hours"]}
                    for o in orders_in
                ],
            }

    return result


# ── quality metrics ──────────────────────────────────────────────────────
def quality_report(result: dict) -> dict:
    """Generate quality metrics for comparing optimizer runs."""
    sched = result.get("order_schedule", [])
    kilns = result.get("kiln_schedule", {})
    summary = result.get("summary", {})

    if not sched:
        return {"score": 0, "explanation": "無排程資料"}

    # 1. Scheduling rate
    scheduled = summary.get("scheduled", 0)
    skipped = summary.get("skipped", 0)
    rate = scheduled / max(scheduled + skipped, 1) * 100

    # 2. Kiln utilization balance (std deviation)
    hours = [k["hours_used"] for k in kilns.values()]
    if len(hours) > 1:
        avg = sum(hours) / len(hours)
        variance = sum((h - avg) ** 2 for h in hours) / len(hours)
        balance = max(0, 100 - (variance ** 0.5) / max(avg, 1) * 50)
    else:
        balance = 100

    # 3. Overdue priority coverage
    overdue = [o for o in sched if o.get("_priority", 0) >= 3.0]
    coverage = len(overdue) / max(summary.get("total_orders", 1), 1) * 100

    # 4. Score
    score = round(rate * 0.4 + balance * 0.3 + coverage * 0.3, 1)

    return {
        "score": score,
        "rate": round(rate, 1),
        "balance": round(balance, 1),
        "overdue_coverage": round(coverage, 1),
        "scheduled": scheduled,
        "skipped": skipped,
        "kilns_used": len(kilns),
        "total_hours": summary.get("total_hours", 0),
    }
