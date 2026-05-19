#!/usr/bin/env python3
"""
生產資料匯入工具 — Excel → SQLite

支援 5 個資料表：orders/products/molds/kilns/processes
用法:
  python3 scripts/import_data.py              # 從 Excel 匯入
  python3 scripts/import_data.py --dry-run    # 預覽不寫入
  python3 scripts/import_data.py --json       # 從 JSON 匯入（原 seed_data 替代）
  python3 scripts/import_data.py --table orders --source data/orders.xlsx
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import SessionLocal, engine, Base
from models import Order, Mold, Kiln, ProcessStep


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MODEL_MAP = {
    "orders": (Order, [
        ("plan_no", str, True),
        ("voltage_kv", float, True),
        ("current_a", float, True),
        ("qty", int, True),
        ("contract_no", str, False),
        ("delivery_date", str, False),
        ("product_from", str, False),
        ("product_to", str, False),
        ("status", str, False),
        ("notes", str, False),
        # Excel date fields need special handling
        ("issue_date", str, False),
        ("unit", str, False),
    ]),
    "molds": (Mold, [
        ("mold_no", str, True),
        ("outer_dia", float, True),
        ("inner_dia", float, True),
        ("length", float, True),
        ("stock_qty", int, False),
        ("location", str, False),
        ("status", str, False),
        ("notes", str, False),
    ]),
    "kilns": (Kiln, [
        ("kiln_no", str, True),
        ("name", str, True),
        ("inner_dia", float, True),
        ("height", float, True),
        ("schemes_json", str, False),
    ]),
    "processes": (ProcessStep, [
        ("step_no", int, True),
        ("step_name", str, True),
        ("department", str, False),
        ("team", str, False),
        ("process_type", str, False),
        ("calc_basis", str, False),
        ("h10", float, False),
        ("h24", float, False),
        ("h36", float, False),
        ("h40", float, False),
    ]),
}


def read_excel(path: str) -> list[dict]:
    """Read an Excel file, return list of row dicts."""
    try:
        import openpyxl
    except ImportError:
        sys.exit("❌ 請安裝 openpyxl: pip install openpyxl")

    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    # First row is header
    headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(rows[0])]
    data = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue
        record = {}
        for i, val in enumerate(row):
            if i < len(headers):
                record[headers[i]] = val
        data.append(record)
    return data


def validate_row(table: str, row: dict, schema: list) -> list[str]:
    """Return list of validation errors for a single row."""
    errors = []
    for field_name, field_type, required in schema:
        if required and (field_name not in row or row[field_name] is None or row[field_name] == ""):
            errors.append(f"缺少必填欄位: {field_name}")
        if field_name in row and row[field_name] is not None and row[field_name] != "":
            try:
                if field_type == int:
                    int(float(row[field_name]))
                elif field_type == float:
                    float(row[field_name])
            except (ValueError, TypeError):
                errors.append(f"{field_name} 格式錯誤，預期 {field_type.__name__}: {row[field_name]}")
    return errors


def import_table(table: str, rows: list[dict], dry_run: bool, db=None) -> dict:
    """Import rows for one table. Return summary dict."""
    model, schema = MODEL_MAP[table]
    summary = {"table": table, "total": len(rows), "imported": 0, "skipped": 0, "errors": 0}

    for idx, row in enumerate(rows):
        errs = validate_row(table, row, schema)
        if errs:
            summary["errors"] += 1
            for e in errs:
                print(f"  ⚠️  第 {idx+2} 行: {e}")
            continue

        if dry_run:
            summary["imported"] += 1
            continue

        try:
            kwargs = {}
            for field_name, field_type, _ in schema:
                if field_name in row and row[field_name] is not None:
                    val = row[field_name]
                    if field_type == int:
                        val = int(float(val))
                    elif field_type == float:
                        val = float(val)
                    kwargs[field_name] = val

            # Check for duplicates (plan_no for orders, mold_no for molds, kiln_no for kilns)
            unique_fields = {"orders": "plan_no", "molds": "mold_no", "kilns": "kiln_no"}
            if table in unique_fields:
                uf = unique_fields[table]
                existing = db.query(model).filter(getattr(model, uf) == kwargs.get(uf)).first()
                if existing:
                    summary["skipped"] += 1
                    continue

            instance = model(**kwargs)
            db.add(instance)
            summary["imported"] += 1
        except Exception as e:
            summary["errors"] += 1
            print(f"  ❌ 第 {idx+2} 行: {e}")

    if not dry_run and summary["imported"] > 0:
        db.commit()
    return summary


def import_from_json(table: str, dry_run: bool, db) -> dict | None:
    """Import from JSON seed data files."""
    json_path = os.path.join(DATA_DIR, f"{table}.json")
    if not os.path.exists(json_path):
        print(f"  ⚠️  {json_path} 不存在，跳過")
        return None

    with open(json_path) as f:
        raw = json.load(f)

    model, schema = MODEL_MAP[table]
    rows = []

    if table == "orders":
        for od in raw:
            if not str(od.get("plan_no", "")):
                continue
            rows.append({
                "plan_no": str(od.get("plan_no", "")),
                "contract_no": str(od.get("contract_no", "") or ""),
                "voltage_kv": float(od.get("voltage_kv", 0) or 0),
                "current_a": float(od.get("current_a", 0) or 0),
                "qty": int(float(od.get("qty", 0) or 0)),
                "delivery_date": str(od.get("delivery_date", "")),
                "product_from": str(od.get("product_from", "")),
                "product_to": str(od.get("product_to", "")),
                "status": "pending",
            })
    elif table == "molds":
        for mold_no, info in raw.items():
            rows.append({
                "mold_no": str(mold_no),
                "outer_dia": float(info.get("od", 0)),
                "inner_dia": float(info.get("id", 0)),
                "length": float(info.get("len", 0)),
                "stock_qty": int(info.get("qty", 0)),
            })
    elif table == "kilns":
        for kiln_no, info in raw.items():
            rows.append({
                "kiln_no": kiln_no,
                "name": str(info.get("name", f"罐{kiln_no}")),
                "inner_dia": float(info.get("inner_dia", 0)),
                "height": float(info.get("height", 0)),
                "schemes_json": json.dumps(info.get("schemes", {}), ensure_ascii=False),
            })
    elif table == "processes":
        for step in raw:
            rows.append({
                "step_no": int(step.get("step", "0").split(".")[0] or 0),
                "step_name": str(step.get("step", "")),
                "department": str(step.get("dept", "")),
                "team": str(step.get("team", "")),
                "process_type": str(step.get("type", "")),
                "calc_basis": str(step.get("calc", "")),
                "h10": float(step.get("h10", 0) or 0),
                "h24": float(step.get("h24", 0) or 0),
                "h36": float(step.get("h36", 0) or 0),
                "h40": float(step.get("h40", 0) or 0),
            })

    return import_table(table, rows, dry_run, db)


def main():
    parser = argparse.ArgumentParser(description="生產資料匯入工具 — Excel/JSON → SQLite")
    parser.add_argument("--dry-run", action="store_true", help="預覽模式，不寫入資料庫")
    parser.add_argument("--json", action="store_true", help="使用 JSON 檔案而非 Excel")
    parser.add_argument("--table", choices=["orders", "products", "molds", "kilns", "processes"],
                        help="只匯入指定資料表")
    parser.add_argument("--source", help="指定 Excel 檔案路徑（覆蓋預設）")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    tables = [args.table] if args.table else ["orders", "molds", "kilns", "processes"]
    mode = "DRY-RUN (預覽)" if args.dry_run else "匯入"
    source_type = "JSON" if args.json else "Excel"

    print(f"╔════════════════════════════════════════╗")
    print(f"║   排爐系統 — {source_type} 資料匯入   ║")
    print(f"║   模式: {mode:28s} ║")
    print(f"╚════════════════════════════════════════╝")
    print()

    totals = {"imported": 0, "skipped": 0, "errors": 0}

    for table in tables:
        print(f"📋 {table}...")
        if args.json:
            result = import_from_json(table, args.dry_run, db)
        else:
            path = args.source or os.path.join(DATA_DIR, f"{table}.xlsx")
            if not os.path.exists(path):
                print(f"  ⚠️  {path} 不存在，跳過")
                continue
            rows = read_excel(path)
            result = import_table(table, rows, args.dry_run, db)

        if result:
            print(f"    {result['imported']} 匯入, {result['skipped']} 跳過, {result['errors']} 錯誤")
            totals["imported"] += result["imported"]
            totals["skipped"] += result["skipped"]
            totals["errors"] += result["errors"]

    print()
    print(f"✅ 完成 — {totals['imported']} 匯入, {totals['skipped']} 跳過, {totals['errors']} 錯誤")

    if args.dry_run:
        print("💡 這是預覽模式，未實際寫入。移除 --dry-run 再做正式匯入。")

    db.close()


if __name__ == "__main__":
    main()