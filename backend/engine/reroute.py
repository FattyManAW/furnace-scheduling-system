"""reroute.py — 動態瓶頸分流模組 (OTD v1.2)

排程後處理層：在 optimizer 初始排程完成後，檢測 congestion（過載爐次），
將過載訂單重新分配到低負載爐次。

原則：只做 detect → redirect，不碰 dispatch policy 層。
對接：Smart P6 CLI ./otd compare --threshold
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime

from engine.optimizer import DAILY_HOUR_CAP


def detect_congestion(
    kiln_schedule: dict,
    threshold_pct: float = 85.0,
    hours_per_root: dict | None = None,
) -> list[dict]:
    """偵測過載爐次。

    Args:
        kiln_schedule: 排程後的 kiln_schedule dict（optimizer 產出）
        threshold_pct: 過載閾值（%）— 爐次使用率超過此值視為 congestion
        hours_per_root: voltage → hours mapping

    Returns:
        [{"kiln_id": "1", "usage_pct": 95, "orders": [...], "excess_hours": 120}, ...]
    """
    congested = []
    for kid, kdata in kiln_schedule.items():
        pct = kdata.get("usage_pct", 0)
        if pct >= threshold_pct:
            congested.append({
                "kiln_id": str(kid),
                "kiln_name": kdata.get("kiln_name", ""),
                "usage_pct": pct,
                "hours_used": kdata.get("hours_used", 0),
                "orders": kdata.get("orders", []),
                "slots_used": kdata.get("slots_used", 0),
                "total_slots": kdata.get("total_slots", 0),
                "excess_hours": max(0, kdata.get("hours_used", 0) - DAILY_HOUR_CAP * threshold_pct / 100),
            })
    # Sort by highest congestion first
    congested.sort(key=lambda x: -x["usage_pct"])
    return congested


def find_alternate_kilns(
    order: dict,
    kilns_data: dict,
    kiln_schedule: dict,
    hours_per_root: dict | None = None,
    max_usage_pct: float = 70.0,
) -> list[dict]:
    """為一筆被移出的訂單找替代爐次。

    Args:
        order: 訂單 dict (plan_no, voltage_kv, qty, mold_od, mold_len, mold_inner_dia)
        kilns_data: 完整 kiln 規格
        kiln_schedule: 當前排程狀態
        hours_per_root: voltage → hours 對照
        max_usage_pct: 目標爐次最高使用率（%）

    Returns:
        [{"kiln_id": "3", "fit_score": 0.23, "usage_pct": 45, "composite": 0.78}, ...]
    """
    from engine.optimizer import fit_score as _fit

    candidates = []
    order.get("voltage_kv", 0)
    order.get("qty", 0)

    for kid, kdata in kiln_schedule.items():
        kid_str = str(kid)

        # Skip if this kiln is also congested
        if kdata.get("usage_pct", 0) >= max_usage_pct:
            continue

        # Check slots available
        if kdata.get("slots_used", 0) >= kdata.get("total_slots", 999):
            continue

        # Fit score
        kiln = kilns_data.get(kid_str, {})
        fscore = _fit(
            kiln,
            mold_od=order.get("mold_od", 0),
            mold_len=order.get("mold_len", 0),
            mold_inner_dia=order.get("mold_inner_dia", order.get("mold_id_dia", 0)),
            needs_big_slot=(order.get("mold_od", 0) >= 470),
        )

        if fscore >= 999:
            continue  # doesn't fit

        # Composite: fit + load balance
        usage = kdata.get("usage_pct", 0)
        composite = fscore + (usage / 100) * 1.5  # prefer less-loaded

        candidates.append({
            "kiln_id": kid_str,
            "kiln_name": kdata.get("kiln_name", ""),
            "fit_score": round(fscore, 3),
            "usage_pct": usage,
            "composite": round(composite, 3),
        })

    candidates.sort(key=lambda x: x["composite"])
    return candidates


def reroute_on_congestion(
    result: dict,
    kilns_data: dict,
    products_by_voltage: dict,
    hours_per_root: dict,
    congestion_threshold: float = 85.0,
    max_iterations: int = 5,
) -> dict:
    """排程後動態分流：從過載爐次移出訂單，分配到低負載爐次。

    Args:
        result: optimizer schedule_orders() 產出的完整 result dict
        kilns_data: 完整爐次規格
        products_by_voltage: voltage → product dicts
        hours_per_root: voltage → hours 對照
        congestion_threshold: 過載閾值（%）
        max_iterations: 最多迭代次數（防止無限重分配）

    Returns:
        修改後的 result dict（含 reroute 統計 + before/after 對比）
    """
    before = {
        "kilns_used": len(result.get("kiln_schedule", {})),
        "congested_kilns": 0,
        "max_usage_pct": 0.0,
        "avg_usage_pct": 0.0,
        "usage_spread": 0.0,
    }

    ks = result.get("kiln_schedule", {})
    if ks:
        pcts = [k["usage_pct"] for k in ks.values()]
        before["max_usage_pct"] = max(pcts)
        before["avg_usage_pct"] = round(sum(pcts) / len(pcts), 1) if pcts else 0
        before["congested_kilns"] = sum(1 for p in pcts if p >= congestion_threshold)
        before["usage_spread"] = round(max(pcts) - min(pcts), 1)

    # Work on a copy
    result = deepcopy(result)
    orders = result.get("order_schedule", [])
    kiln_schedule = result["kiln_schedule"]
    result.setdefault("reroute", {"iterations": 0, "moved": 0, "before": before, "after": {}})

    moved_count = 0

    for iteration in range(max_iterations):
        congested = detect_congestion(kiln_schedule, congestion_threshold)
        if not congested:
            break

        result["reroute"]["iterations"] = iteration + 1
        moved_this_round = 0

        for c in congested:
            c_orders = c.get("orders", [])
            if not c_orders:
                continue

            # Try to move the last (largest hours) order from each congested kiln
            # Sort orders by est_hours descending to move biggest first
            c_orders_sorted = sorted(c_orders, key=lambda o: o.get("hours", 0), reverse=True)

            for o_summary in c_orders_sorted[:1]:  # Move at most 1 per congested kiln per iteration
                plan_no = o_summary.get("plan_no", "")
                full_order = next((o for o in orders if o.get("plan_no") == plan_no), None)
                if not full_order:
                    continue

                alts = find_alternate_kilns(
                    full_order, kilns_data, kiln_schedule, hours_per_root,
                    max_usage_pct=congestion_threshold,
                )
                if not alts:
                    continue

                # Move to best alternate
                alt = alts[0]
                old_kiln_id = full_order.get("kiln_id", "")
                new_kiln_id = alt["kiln_id"]

                # Update order
                old_hours = full_order.get("est_hours", 0)
                full_order["kiln_id"] = new_kiln_id
                full_order["kiln_name"] = alt["kiln_name"]
                full_order["_rerouted_from"] = old_kiln_id
                full_order["_rerouted_at"] = datetime.now().strftime("%H:%M:%S")

                # Update kiln schedules
                old_k = kiln_schedule.get(old_kiln_id)
                if old_k:
                    old_k["slots_used"] = max(0, old_k.get("slots_used", 0) - 1)
                    old_k["hours_used"] = max(0, old_k.get("hours_used", 0) - old_hours)
                    old_k["order_count"] = max(0, old_k.get("order_count", 0) - 1)
                    old_k["orders"] = [o for o in old_k.get("orders", []) if o.get("plan_no") != plan_no]
                    old_usage = old_k["hours_used"] / max(DAILY_HOUR_CAP, 1) * 100
                    old_k["usage_pct"] = min(round(old_usage, 1), 100)

                new_k = kiln_schedule.get(new_kiln_id)
                if new_k:
                    new_k["slots_used"] = new_k.get("slots_used", 0) + 1
                    new_k["hours_used"] = new_k.get("hours_used", 0) + old_hours
                    new_k["order_count"] = new_k.get("order_count", 0) + 1
                    new_orders = list(new_k.get("orders", []))
                    new_orders.append(o_summary)
                    new_k["orders"] = new_orders
                    new_usage = new_k["hours_used"] / max(DAILY_HOUR_CAP, 1) * 100
                    new_k["usage_pct"] = min(round(new_usage, 1), 100)

                moved_count += 1
                moved_this_round += 1

        if moved_this_round == 0:
            break

    # Build after stats
    after = {
        "kilns_used": len(kiln_schedule),
        "congested_kilns": 0,
        "max_usage_pct": 0.0,
        "avg_usage_pct": 0.0,
        "usage_spread": 0.0,
    }
    if kiln_schedule:
        pcts = [k["usage_pct"] for k in kiln_schedule.values()]
        after["max_usage_pct"] = max(pcts) if pcts else 0
        after["avg_usage_pct"] = round(sum(pcts) / len(pcts), 1) if pcts else 0
        after["congested_kilns"] = sum(1 for p in pcts if p >= congestion_threshold)
        after["usage_spread"] = round(max(pcts) - min(pcts), 1) if pcts else 0

    result["reroute"].update({
        "moved": moved_count,
        "after": after,
    })

    return result


def reroute_report(result: dict) -> str:
    """產生 before/after 文字報告（CI / board chat 用）。"""
    rr = result.get("reroute", {})
    if not rr:
        return "⚠️ 無 reroute 數據"

    before = rr.get("before", {})
    after = rr.get("after", {})
    moved = rr.get("moved", 0)
    iterations = rr.get("iterations", 0)

    lines = [
        "═══════════════════════════════════",
        "  reroute_on_congestion Report",
        "═══════════════════════════════════",
        f"  Iterations:  {iterations}",
        f"  Orders Moved: {moved}",
        "",
        "  ── Before ───────────────────────",
        f"  Congested Kilns:  {before.get('congested_kilns', '?')}",
        f"  Max Usage:        {before.get('max_usage_pct', '?')}%",
        f"  Avg Usage:        {before.get('avg_usage_pct', '?')}%",
        f"  Usage Spread:     {before.get('usage_spread', '?')}%",
        "",
        "  ── After ────────────────────────",
        f"  Congested Kilns:  {after.get('congested_kilns', '?')}",
        f"  Max Usage:        {after.get('max_usage_pct', '?')}%",
        f"  Avg Usage:        {after.get('avg_usage_pct', '?')}%",
        f"  Usage Spread:     {after.get('usage_spread', '?')}%",
        "",
    ]

    # Improvement stats
    before_max = before.get("max_usage_pct", 0)
    after_max = after.get("max_usage_pct", 0)
    before_spread = before.get("usage_spread", 0)
    after_spread = after.get("usage_spread", 0)

    if moved > 0:
        lines.append(f"  ✅ Max usage: {before_max}% → {after_max}% ({(before_max - after_max):.1f}% improvement)")
        lines.append(f"  ✅ Spread:     {before_spread}% → {after_spread}% ({(before_spread - after_spread):.1f}% narrower)")
    else:
        lines.append("  ℹ️  No congestion detected — all kilns within threshold")

    lines.append("═══════════════════════════════════")
    return "\n".join(lines)
