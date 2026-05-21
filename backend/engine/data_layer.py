"""統一資料層 — 從 DB 載入排程所需的所有參考數據。

取代 optimizer._load_data() 的 JSON 直接讀取，
讓 JSON files 降級為 seed-only。
"""
from __future__ import annotations

import contextlib
import json

from models import Kiln as KilnModel
from models import ProcessStep as ProcessStepModel
from models import Product as ProductModel
from sqlalchemy.orm import Session


def load_products_by_voltage(db: Session) -> dict:
    """從 DB 的 products 表載入，轉換為 voltage → product dicts 對照表。"""
    rows = db.query(ProductModel).order_by(ProductModel.voltage_kv).all()
    product_dicts = [
        {
            "voltage_kv": r.voltage_kv,
            "current_a": r.current_a or 0,
            "mold_od": r.mold_od,
            "mold_id": r.mold_id or 0,
            "mold_len": r.mold_len,
            "capacity": r.capacity or 1,
        }
        for r in rows
    ]
    by_v: dict[float, list[dict]] = {}
    for p in product_dicts:
        v = round(float(p.get("voltage_kv", 0)), 1)
        if v > 0:
            by_v.setdefault(v, []).append(p)
    return by_v


def load_hours_per_root(db: Session) -> dict:
    """從 DB 的 process_steps 表計算各電壓等級總工時。"""
    rows = db.query(ProcessStepModel).all()
    h10 = sum(float(r.h10 or 0) for r in rows)
    h24 = sum(float(r.h24 or 0) for r in rows)
    h36 = sum(float(r.h36 or 0) for r in rows)
    h40 = sum(float(r.h40 or 0) for r in rows)
    return {10: h10, 24: h24, 36: h36, 40: h40}


def load_kilns_data(db: Session) -> dict:
    """從 DB 的 kilns 表載入，轉換為 optimizer 相容的 dict 格式。"""
    rows = db.query(KilnModel).order_by(KilnModel.id).all()
    kilns = {}
    for r in rows:
        schemes = {}
        if r.schemes_json:
            with contextlib.suppress(json.JSONDecodeError, TypeError):
                schemes = json.loads(r.schemes_json)
        kilns[str(r.kiln_no)] = {
            "name": r.name,
            "inner_dia": r.inner_dia,
            "height": r.height,
            "schemes": schemes,
        }
    return kilns


def load_all_optimizer_data(db: Session) -> tuple[dict, dict, dict]:
    """一次載入 optimizer 所需的三項數據。

    Returns:
        (products_by_voltage, kilns_data, hours_per_root)
    """
    return (
        load_products_by_voltage(db),
        load_kilns_data(db),
        load_hours_per_root(db),
    )
