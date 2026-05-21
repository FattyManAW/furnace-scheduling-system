"""Reports API — CSV 匯出與儀表板統計"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from typing import Optional

from crud import get_orders
from engine.optimizer import DAILY_HOUR_CAP
from fastapi import APIRouter, Depends, Query, Response
from models import Kiln, Mold, Order, ScheduleEntry
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    today = date.today().isoformat()

    total_orders = db.query(Order).count()
    pending = db.query(Order).filter(Order.status == "pending").count()
    scheduled = db.query(Order).filter(Order.status == "scheduled").count()
    completed = db.query(Order).filter(Order.status == "completed").count()
    overdue = db.query(Order).filter(
        Order.delivery_date < today, Order.status != "completed"
    ).count()

    total_kilns = db.query(Kiln).count()
    active_kilns = db.query(ScheduleEntry.kiln_id).distinct().count()
    total_molds = db.query(Mold).count()

    s_entries = db.query(ScheduleEntry).all()
    total_hours = round(sum(e.est_hours for e in s_entries), 1)

    # Overdue orders detail
    overdue_orders = db.query(Order).filter(
        Order.delivery_date < today, Order.status != "completed"
    ).order_by(Order.delivery_date).all()

    # Today's schedule
    today_entries = [e for e in s_entries if e.delivery_date and e.delivery_date == today]

    # Pending by contract
    pending_orders = db.query(Order).filter(Order.status == "pending").all()
    pending_by_contract: dict = {}
    for o in pending_orders:
        c = o.contract_no or "未分類"
        pending_by_contract.setdefault(c, {"count": 0, "qty": 0})
        pending_by_contract[c]["count"] += 1
        pending_by_contract[c]["qty"] += o.qty or 0

    return {
        "orders": {
            "total": total_orders,
            "pending": pending,
            "scheduled": scheduled,
            "completed": completed,
            "overdue": overdue,
            "pending_by_contract": [
                {"contract": k, **v}
                for k, v in sorted(pending_by_contract.items())
            ],
        },
        "kilns": {
            "total": total_kilns,
            "active_today": active_kilns,
        },
        "molds": {"total": total_molds},
        "schedule": {
            "total_hours": total_hours,
            "daily_cap": DAILY_HOUR_CAP,
            "hours_remaining": max(0, round(DAILY_HOUR_CAP - sum(e.est_hours for e in today_entries), 1)),
            "today_entries": len(today_entries),
        },
        "overdue_orders": [
            {
                "id": o.id, "plan_no": o.plan_no,
                "contract_no": o.contract_no,
                "delivery_date": o.delivery_date,
                "qty": o.qty,
            }
            for o in overdue_orders
        ],
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/orders/csv")
def export_orders_csv(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    orders = get_orders(db, limit=9999, status=status)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "plan_no", "contract_no", "voltage_kv", "current_a",
        "qty", "delivery_date", "status", "product_from", "product_to",
        "created_at", "updated_at",
    ])
    for o in orders:
        writer.writerow([
            o.id, o.plan_no, o.contract_no, o.voltage_kv, o.current_a,
            o.qty, o.delivery_date, o.status, o.product_from, o.product_to,
            o.created_at, o.updated_at,
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"},
    )


@router.get("/schedule/csv")
def export_schedule_csv(db: Session = Depends(get_db)):
    entries = db.query(ScheduleEntry).order_by(ScheduleEntry.kiln_id).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "kiln_id", "plan_no", "contract_no", "voltage_kv",
        "qty", "delivery_date", "mold_od", "mold_len",
        "est_hours", "status",
    ])
    for e in entries:
        writer.writerow([
            e.id, e.kiln_id, e.plan_no, e.contract_no, e.voltage_kv,
            e.qty, e.delivery_date, e.mold_od, e.mold_len,
            e.est_hours, e.status,
        ])
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule.csv"},
    )


@router.get("/orders/json")
def export_orders_json(db: Session = Depends(get_db)):
    orders = get_orders(db, limit=9999)
    data = [
        {
            "id": o.id, "plan_no": o.plan_no, "contract_no": o.contract_no,
            "voltage_kv": o.voltage_kv, "current_a": o.current_a,
            "qty": o.qty, "delivery_date": o.delivery_date,
            "status": o.status, "product_from": o.product_from,
            "product_to": o.product_to, "created_at": str(o.created_at),
            "updated_at": str(o.updated_at),
        }
        for o in orders
    ]
    return {"orders": data, "exported_at": datetime.now().isoformat()}
