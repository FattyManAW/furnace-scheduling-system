"""
oven_scheduler/data_loader.py
Parse all source Excel files into structured JSON-serializable data.
"""
import xlrd, json, os, math
from datetime import datetime, timedelta

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "data")

# ── Module-level caches (populated by load_all()) ──────────────────────────
_PRODUCTS = None
_PROCESS_STEPS = None
_DAILY_LIMITS = None
_ORDERS = None
_MOLD_INVENTORY = None
_DRYERS = None
_MOLD_LOOKUP = None

def _excel_date(v):
    if isinstance(v, float) and v > 40000:
        return (datetime(1899, 12, 30) + timedelta(days=int(v))).strftime("%Y-%m-%d")
    return str(v)

# ─── 1. 產品規格表 (File 5 + File 1 partial) ───────────────────────────
def load_products():
    """Map voltage/current → product spec (outer/inner/length, hours per process)."""
    wb = xlrd.open_workbook(os.path.join(BASE, "5.产品与模具对照表-2026-4-15.xls"))
    sh = wb.sheet_by_index(0)
    products = {}
    for r in range(2, sh.nrows):
        vals = [sh.cell_value(r, c) for c in range(sh.ncols)]
        seq, kv, amp, od, idd, length = (vals[0], vals[1], vals[2], vals[3], vals[4], vals[5])
        if not isinstance(kv, (int, float)):
            continue
        key = (float(kv), float(amp))
        products[key] = {
            "seq": int(seq) if seq else None,
            "voltage_kv": float(kv),
            "current_a": float(amp),
            "mold_od": float(od),
            "mold_id": float(idd),
            "mold_length": float(length),
            "units_per_bundle": int(vals[6]) if vals[6] else 1,
        }
    return products

# ─── 2. 加工工時 (File 1) ─────────────────────────────────────────────
def load_process_times():
    """Per-voltage processing times for each step (in hours)."""
    wb = xlrd.open_workbook(os.path.join(BASE, "1. 产品作业流程及工时-2026-4-15.xls"))
    sh = wb.sheet_by_index(0)
    # Voltage columns start at index 8, step 2
    voltage_cols = {}
    for c in range(7, sh.ncols, 2):
        if c + 1 < sh.ncols:
            kv = sh.cell_value(1, c)   # e.g. "人\n\n数" header is row 1, actual kv in row 0
            # Voltage header is actually row 0
            kv2 = sh.cell_value(0, c)
            try:
                voltage_cols[c] = float(kv2)
            except:
                voltage_cols[c] = kv2

    steps = []
    for r in range(2, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        flow = row[0]
        sub = row[1]
        name = row[5]
        calc = row[6]
        if not name:
            continue
        # Get a sample per-voltage for reference
        sample = {}
        for c in range(8, min(42, sh.ncols), 2):
            if c+1 < sh.ncols:
                try:
                    h = float(row[c+1])
                    kv = float(sh.cell_value(0, c)) if c < sh.ncols else 0
                    if kv > 0 and h > 0:
                        sample[kv] = h
                except:
                    pass
        steps.append({
            "step": name,
            "flow": flow,
            "sub": sub,
            "calc": calc,
            "per_voltage_h": sample,
        })
    return steps

# ─── 3. 每日工時上限 (File 3) ─────────────────────────────────────────
def load_daily_limits():
    """Per-department daily work-hour cap."""
    wb = xlrd.open_workbook(os.path.join(BASE, "3.各工序每日理论总工时上限-2026-4-15.xls"))
    sh = wb.sheet_by_index(0)
    dept_limits = []
    for r in range(2, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        if row[0] == "合计":
            continue
        try:
            total = float(row[8])
            if total > 0:
                dept_limits.append({
                    "dept": str(row[0]).strip(),
                    "team": str(row[1]).replace("\n","").strip() + " / " + str(row[2]).replace("\n","").strip(),
                    "role": str(row[4]).strip(),
                    "headcount": float(row[5]) if row[5] else 0,
                    "shifts": str(row[6]).strip(),
                    "hours_per_shift": float(row[7]) if row[7] else 0,
                    "daily_total": total,
                })
        except:
            pass
    return dept_limits

# ─── 4. 訂單 (File 4) ────────────────────────────────────────────────
def load_orders():
    wb = xlrd.open_workbook(os.path.join(BASE, "4.生产订单排产模拟信息-2026-4-15.xls"))
    sh = wb.sheet_by_index(0)
    orders = []
    for r in range(2, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        try:
            orders.append({
                "order_id": str(row[1]) if row[1] else f"ORD-{r}",
                "contract": str(row[2]),
                "voltage_kv": float(row[3]),
                "current_a": float(row[4]),
                "unit": str(row[5]),
                "qty": int(row[6]),
                "delivery_date": _excel_date(row[7]),
                "product_start": int(row[8]) if row[8] else 0,
                "product_end": int(row[9]) if row[9] else 0,
            })
        except:
            pass
    return orders

# ─── 5. 模具庫存 (File 6) ───────────────────────────────────────────
def load_mold_inventory():
    wb = xlrd.open_workbook(os.path.join(BASE, "6.入罐模具台账-2026-4-15.xls"))
    sh = wb.sheet_by_index(0)
    molds = []
    for r in range(2, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        try:
            molds.append({
                "id": int(row[0]),
                "od": float(row[1]),
                "id_inner": float(row[2]),
                "length": float(row[3]),
                "qty": int(row[4]),
            })
        except:
            pass
    return molds

# ─── 6. 乾燥罐配置 (File 2) ─────────────────────────────────────────
def load_dryers():
    wb = xlrd.open_workbook(os.path.join(BASE, "2. 干燥罐与模具对照表-2026-4-15.xls"))
    sh = wb.sheet_by_index(0)
    dryers = []
    current = None
    for r in range(3, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        seq = row[0]
        name = row[1]
        inner_d = row[2]
        height = row[3]
        plan = row[4]
        # Upper mold
        u_qty = row[5] if row[5] != "－" and row[5] != "" else 0
        u_od = row[6] if row[6] != "－" else 0
        u_id2 = row[7] if row[7] != "－" else 0
        u_len = row[8] if row[8] != "－" else 0
        # Lower mold
        l_qty = row[9] if row[9] != "－" and row[9] != "" else 0
        l_od = row[10] if row[10] != "－" else 0
        l_id2 = row[11] if row[11] != "－" else 0
        l_len = row[12] if row[12] != "－" else 0

        if isinstance(seq, float) and seq > 0:
            if current:
                dryers.append(current)
            current = {
                "id": int(seq),
                "name": str(name).strip(),
                "inner_d": float(inner_d),
                "height": float(height),
                "plans": [],
            }
        if current and plan:
            try:
                current["plans"].append({
                    "plan": str(plan).strip(),
                    "upper": {"qty": int(u_qty), "od": float(u_od), "id": float(u_id2), "length": float(u_len)},
                    "lower": {"qty": int(l_qty), "od": float(l_od), "id": float(l_id2), "length": float(l_len)},
                })
            except:
                pass
    if current:
        dryers.append(current)
    # Deduplicate plans per dryer
    for d in dryers:
        seen = {}
        deduped = []
        for p in d["plans"]:
            k = p["plan"]
            if k not in seen:
                seen[k] = p
                deduped.append(p)
        d["plans"] = deduped
    return dryers


def load_all():
    global _PRODUCTS, _PROCESS_STEPS, _DAILY_LIMITS, _ORDERS, _MOLD_INVENTORY, _DRYERS, _MOLD_LOOKUP
    _PRODUCTS = load_products()
    _PROCESS_STEPS = load_process_times()
    _DAILY_LIMITS = load_daily_limits()
    _ORDERS = load_orders()
    _MOLD_INVENTORY = load_mold_inventory()
    _DRYERS = load_dryers()
    # Build mold lookup: (od,id,length) → total qty
    _MOLD_LOOKUP = {}
    for m in _MOLD_INVENTORY:
        key = (round(m["od"], 1), round(m["id_inner"], 1), round(m["length"], 1))
        _MOLD_LOOKUP[key] = m["qty"]
    return {
        "products": _PRODUCTS,
        "process_steps": _PROCESS_STEPS,
        "daily_limits": _DAILY_LIMITS,
        "orders": _ORDERS,
        "mold_inventory": _MOLD_INVENTORY,
        "dryers": _DRYERS,
    }

if __name__ == "__main__":
    data = load_all()
    print(json.dumps({k: (len(v) if isinstance(v, list) else len(v)) for k, v in data.items()}, ensure_ascii=False, indent=2))
    # Print dryer summary
    print(f"\nDryers: {len(data['dryers'])}")
    for d in data['dryers'][:3]:
        print(f"  {d['name']} ({d['inner_d']}×{d['height']}mm) → {len(d['plans'])} plans")
    print(f"\nProducts: {len(data['products'])}")
    print(f"Orders: {len(data['orders'])}")
    print(f"Molds: {len(data['mold_inventory'])}")
