"""Schedule API — 排程執行與結果查詢 + 單筆管理"""
import json
from typing import Optional as _Opt
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Order, ScheduleEntry, Kiln
from schemas import ScheduleRequest, ScheduleResult, ScheduleEntryOut, PaginatedResponse
from crud import (
    get_orders, clear_schedule, create_schedule_entry, get_kilns,
    get_kiln as get_kiln_crud,
)
from engine.optimizer import schedule_orders, hours_for, DAILY_HOUR_CAP
from engine.validator import validate_schedule

router = APIRouter(prefix="/api/v1/schedule", tags=["schedule"])

_kiln_name_cache: dict = {}

def _kiln_name(db: Session, kiln_id: int) -> str:
    if not kiln_id:
        return ""
    if kiln_id in _kiln_name_cache:
        return _kiln_name_cache[kiln_id]
    k = db.query(Kiln).filter(Kiln.id == kiln_id).first()
    name = k.name if k else ""
    _kiln_name_cache[kiln_id] = name
    return name


@router.post("/optimize", response_model=ScheduleResult)
def run_schedule(request: ScheduleRequest, db: Session = Depends(get_db)):
    """執行排程優化，清除舊排程，寫入新結果"""
    if request.order_ids:
        orders = db.query(Order).filter(Order.id.in_(request.order_ids)).all()
    else:
        orders = db.query(Order).order_by(Order.id).all()

    if not orders:
        raise HTTPException(400, "無可用訂單")

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

    result = schedule_orders(order_dicts)

    validation = validate_schedule(result)
    if not validation["valid"]:
        result["warnings"].extend([f"[驗證錯誤] {e}" for e in validation["errors"]])

    clear_schedule(db)
    kiln_map = {str(k.kiln_no): k for k in get_kilns(db)}
    current_a_map = {}

    for entry in result["order_schedule"]:
        kid_str = str(entry["kiln_id"])
        db_kiln = kiln_map.get(kid_str)
        if not db_kiln:
            for _k in get_kilns(db):
                if str(_k.kiln_no) == kid_str or str(_k.id) == kid_str:
                    db_kiln = _k
                    break
        kiln_id = db_kiln.id if db_kiln else None

        db_order = db.query(Order).filter(Order.plan_no == entry["plan_no"]).first()
        order_id = db_order.id if db_order else None

        _current_a = float(db_order.current_a) if db_order and db_order.current_a is not None else float(entry.get("current_a", 0) or 0)
        current_a_map[entry["plan_no"]] = _current_a
        _deliv = str(entry.get("delivery_date", ""))
        if len(_deliv) >= 10:
            try:
                _deliv = datetime.strptime(_deliv[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
            except Exception:
                try:
                    _deliv = datetime.strptime(_deliv[:10], "%Y/%m/%d").strftime("%Y-%m-%d")
                except Exception:
                    pass

        create_schedule_entry(db, {
            "kiln_id": kiln_id,
            "order_id": order_id,
            "plan_no": entry["plan_no"],
            "contract_no": entry.get("contract_no", ""),
            "voltage_kv": entry["voltage_kv"],
            "current_a": _current_a,
            "qty": entry["qty"],
            "delivery_date": _deliv,
            "mold_od": entry.get("mold_od", 0),
            "mold_len": entry.get("mold_len", 0),
            "est_hours": entry.get("est_hours", 0),
            "status": entry.get("status", "scheduled"),
            "notes": "",
        })

        if db_order:
            db_order.status = "scheduled"
            db_order.updated_at = datetime.utcnow()

    db.commit()

    _fresh_entries = db.query(ScheduleEntry).order_by(ScheduleEntry.id).all()
    id_map = {}
    for fe in _fresh_entries:
        id_map[fe.plan_no] = fe.id

    schedule_out = [
        ScheduleEntryOut(
            id=id_map.get(e["plan_no"], 0),
            kiln_id=int(e["kiln_id"]) if str(e["kiln_id"]).isdigit() else 0,
            kiln_name=e.get("kiln_name"),
            plan_no=e["plan_no"],
            contract_no=e.get("contract_no"),
            voltage_kv=e["voltage_kv"],
            current_a=current_a_map.get(e["plan_no"], 0),
            qty=e["qty"],
            delivery_date=e.get("delivery_date"),
            mold_od=e.get("mold_od", 0),
            mold_len=e.get("mold_len", 0),
            est_hours=e.get("est_hours", 0),
            status=e.get("status", "scheduled"),
            created_at=next((fe.created_at for fe in _fresh_entries if fe.plan_no == e["plan_no"]), None),
        )
        for e in result["order_schedule"]
    ]

    return ScheduleResult(
        summary=result["summary"],
        kiln_summary=list(result["kiln_schedule"].values()),
        schedule=schedule_out,
        warnings=result["warnings"],
    )


@router.get("/result", response_model=ScheduleResult)
def get_schedule_result(db: Session = Depends(get_db)):
    """取得當前排程結果"""
    entries = db.query(ScheduleEntry).all()
    if not entries:
        raise HTTPException(404, "尚無排程結果，請先執行排程")

    summary_map = {}
    kiln_summary_map = {}

    for e in entries:
        summary_map["scheduled"] = summary_map.get("scheduled", 0) + 1
        summary_map["total_hours"] = summary_map.get("total_hours", 0) + e.est_hours
        kid = e.kiln_id
        if kid not in kiln_summary_map:
            kiln_summary_map[kid] = {
                "kiln_id": kid,
                "slots_used": 0,
                "hours_used": 0.0,
                "order_count": 0,
            }
        kiln_summary_map[kid]["slots_used"] += 1
        kiln_summary_map[kid]["hours_used"] += e.est_hours
        kiln_summary_map[kid]["order_count"] += 1

    summary_map["total_hours"] = round(summary_map.get("total_hours", 0), 1)
    summary_map["daily_cap"] = DAILY_HOUR_CAP
    summary_map["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    for kid, k in kiln_summary_map.items():
        pct = round(k["hours_used"] / DAILY_HOUR_CAP * 100, 1) if DAILY_HOUR_CAP > 0 else 0
        k["usage_pct"] = min(pct, 100)

    schedule_out = [
        ScheduleEntryOut(
            id=e.id, kiln_id=e.kiln_id,
            kiln_name=_kiln_name(db, e.kiln_id),
            plan_no=e.plan_no,
            contract_no=e.contract_no, voltage_kv=e.voltage_kv,
            current_a=e.current_a, qty=e.qty,
            delivery_date=e.delivery_date, mold_od=e.mold_od,
            mold_len=e.mold_len, est_hours=e.est_hours,
            status=e.status, created_at=e.created_at,
        )
        for e in entries
    ]

    return ScheduleResult(
        summary=summary_map,
        kiln_summary=list(kiln_summary_map.values()),
        schedule=schedule_out,
        warnings=[],
    )


@router.get("/{kiln_id}/schedule")
def get_kiln_schedule(kiln_id: int, db: Session = Depends(get_db)):
    entries = db.query(ScheduleEntry).filter(ScheduleEntry.kiln_id == kiln_id).all()
    k = get_kiln_crud(db, kiln_id)
    if not k:
        raise HTTPException(404, "干燥罐不存在")
    return {
        "kiln_id": kiln_id,
        "kiln_name": k.name,
        "entries": [
            {
                "plan_no": e.plan_no,
                "contract_no": e.contract_no,
                "voltage_kv": e.voltage_kv,
                "qty": e.qty,
                "delivery_date": e.delivery_date,
                "est_hours": e.est_hours,
                "status": e.status,
            }
            for e in entries
        ],
    }


# ── Schedule Entry 單筆管理 ──────────────────────────────────────────────
@router.get("/entries", response_model=PaginatedResponse[ScheduleEntryOut])
def list_schedule_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    kiln_id: _Opt[int] = Query(None),
    db: Session = Depends(get_db),
):
    """列出所有排程記錄，支援分頁與窯爐篩選"""
    q = db.query(ScheduleEntry)
    if kiln_id is not None:
        q = q.filter(ScheduleEntry.kiln_id == kiln_id)
    total = q.count()
    entries = q.order_by(ScheduleEntry.id).offset(skip).limit(limit).all()
    return PaginatedResponse(items=entries, total=total, skip=skip, limit=limit)


@router.get("/entries/{entry_id}", response_model=ScheduleEntryOut)
def get_schedule_entry(entry_id: int, db: Session = Depends(get_db)):
    """取得單筆排程記錄"""
    entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "排程記錄不存在")
    return entry


@router.delete("/entries/{entry_id}")
def remove_schedule_entry(entry_id: int, db: Session = Depends(get_db)):
    """刪除單筆排程記錄"""
    entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "排程記錄不存在")
    db.delete(entry)
    db.commit()
    return {"deleted": True, "entry_id": entry_id}


@router.delete("/clear")
def clear_all_schedule(db: Session = Depends(get_db)):
    """清除所有排程記錄"""
    cnt = clear_schedule(db)
    return {"deleted": True, "count": cnt}
