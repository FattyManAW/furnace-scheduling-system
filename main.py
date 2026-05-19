from __future__ import annotations
"""
oven_scheduler/main.py
FastAPI application — Best-Fit Furnace Scheduling System.
"""
import json, os, csv, io
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from database import init_db, make_get_db, Dryer, DryerPlan, MoldType, ProductSpec, Order, Batch, Base
from engine import run_schedule

# ─── Config ────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scheduler.db")
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
init_db(engine)

get_db = make_get_db(engine)



# ─── App ───────────────────────────────────────────────────────
app = FastAPI(
    title="乾式套管最佳排爐系統",
    description="根據訂單、模具庫存與乾燥罐規格，自動計算最佳排爐方案。",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    # TODO: production → replace with actual frontend origin(s)
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Pydantic Schemas ──────────────────────────────────────────
class OrderIn(BaseModel):
    order_id: str
    contract_no: Optional[str] = ""
    voltage_kv: float
    current_a: float
    unit: Optional[str] = "支"
    quantity: int
    delivery_date: str
    product_start: int = 0
    product_end: int = 0

class ScheduleRequest(BaseModel):
    order_ids: Optional[list[str]] = None
    furnaces: Optional[list[str]] = None

class BatchUpdate(BaseModel):
    is_selected: bool

# ─── Static Files ─────────────────────────────────────────────
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html"))


# ─── Summary ──────────────────────────────────────────────────
@app.get("/api/summary")
def api_summary(db: Session = Depends(get_db)):
    return {
        "dryers_count": db.query(Dryer).count(),
        "plans_count": db.query(DryerPlan).count(),
        "molds_count": db.query(MoldType).count(),
        "products_count": db.query(ProductSpec).count(),
        "orders_count": db.query(Order).count(),
        "batches_count": db.query(Batch).count(),
    }


# ─── Dryers ───────────────────────────────────────────────────
@app.get("/api/dryers")
def api_dryers(db: Session = Depends(get_db)):
    result = []
    for d in db.query(Dryer).order_by(Dryer.id).all():
        result.append({
            "id": d.id,
            "name": d.name,
            "inner_d": d.inner_diameter,
            "height": d.height,
            "plans": [
                {
                    "plan": p.plan_label,
                    "upper": {"qty": p.upper_qty, "od": p.upper_od, "id": p.upper_id, "length": p.upper_length},
                    "lower": {"qty": p.lower_qty, "od": p.lower_od, "id": p.lower_id, "length": p.lower_length},
                }
                for p in sorted(d.plans, key=lambda x: x.plan_label)
            ],
        })
    return result


@app.get("/api/dryers/{name}")
def api_dryer_detail(name: str, db: Session = Depends(get_db)):
    d = db.query(Dryer).filter(Dryer.name == name).first()
    if not d:
        raise HTTPException(404, "Dryer not found")
    return {
        "id": d.id,
        "name": d.name,
        "inner_d": d.inner_diameter,
        "height": d.height,
        "plans": [
            {
                "plan": p.plan_label,
                "upper": {"qty": p.upper_qty, "od": p.upper_od, "id": p.upper_id, "length": p.upper_length},
                "lower": {"qty": p.lower_qty, "od": p.lower_od, "id": p.lower_id, "length": p.lower_length},
            }
            for p in sorted(d.plans, key=lambda x: x.plan_label)
        ],
    }


# ─── Molds ────────────────────────────────────────────────────
@app.get("/api/molds")
def api_molds(db: Session = Depends(get_db)):
    return [
        {
            "id": m.id,
            "od": m.outer_diameter,
            "id_inner": m.inner_diameter,
            "length": m.length,
            "qty": m.quantity,
            "is_active": m.is_active,
        }
        for m in db.query(MoldType).order_by(MoldType.outer_diameter.desc()).all()
    ]


# ─── Products ─────────────────────────────────────────────────
@app.get("/api/products")
def api_products(db: Session = Depends(get_db)):
    products = {}
    for p in db.query(ProductSpec).all():
        key = f"{p.voltage_kv}kV/{p.current_a}A"
        products[key] = {
            "seq": p.id,
            "voltage_kv": p.voltage_kv,
            "current_a": p.current_a,
            "mold_od": p.mold_od,
            "mold_id": p.mold_id,
            "mold_length": p.mold_length,
            "units_per_bundle": p.units_per_bundle,
        }
    return products


@app.get("/api/products/{label}")
def api_product_detail(label: str, db: Session = Depends(get_db)):
    p = db.query(ProductSpec).filter(ProductSpec.label == label).first()
    if not p:
        raise HTTPException(404, "Product not found")
    return {
        "voltage_kv": p.voltage_kv,
        "current_a": p.current_a,
        "mold_od": p.mold_od,
        "mold_id": p.mold_id,
        "mold_length": p.mold_length,
        "units_per_bundle": p.units_per_bundle,
        "label": p.label,
    }


# ─── Mold Match ───────────────────────────────────────────────
class MoldMatchRequest(BaseModel):
    voltage_kv: float
    current_a: float


@app.post("/api/mold-match")
def api_mold_match(req: MoldMatchRequest, db: Session = Depends(get_db)):
    ms = get_mold_for_product(req.voltage_kv, req.current_a)
    if ms:
        return {"mold_spec": {"od": ms[0], "id": ms[1], "length": ms[2]}}
    return {"mold_spec": None}


# ─── Orders ───────────────────────────────────────────────────
@app.get("/api/orders")
def api_orders(
    start: Optional[str] = None,
    end: Optional[str] = None,
    selected: Optional[bool] = None,
    kv: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if start:
        query = query.filter(Order.delivery_date >= start)
    if end:
        query = query.filter(Order.delivery_date <= end)
    if selected is not None:
        query = query.filter(Order.is_selected == selected)
    if kv:
        query = query.filter(Order.voltage_kv == kv)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Order.order_id.like(like)) | (Order.contract_no.like(like))
        )
    return [
        {
            "id": o.id,
            "order_id": o.order_id,
            "contract_no": o.contract_no,
            "voltage_kv": o.voltage_kv,
            "current_a": o.current_a,
            "unit": o.unit,
            "quantity": o.quantity,
            "delivery_date": o.delivery_date,
            "product_start": o.product_start,
            "product_end": o.product_end,
            "is_selected": o.is_selected,
        }
        for o in query.order_by(Order.delivery_date.asc()).all()
    ]


@app.patch("/api/orders/{order_id}")
def api_order_toggle(order_id: str, body: BatchUpdate, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.order_id == order_id).first()
    if not o:
        raise HTTPException(404, "Order not found")
    o.is_selected = body.is_selected
    db.commit()
    return {"order_id": o.order_id, "is_selected": o.is_selected}


# ─── Process Steps ────────────────────────────────────────────
@app.get("/api/process-steps")
def api_process_steps(db: Session = Depends(get_db)):
    return [
        {
            "id": s.id,
            "step": s.step_name,
            "flow": s.flow,
            "sub": s.sub_flow,
            "calc": s.calc_method,
            "per_voltage_h": json.loads(s.per_voltage_hours) if s.per_voltage_hours else {},
        }
        for s in db.query(ProcessStep).order_by(ProcessStep.sort_order).all()
    ]


# ─── Optimize ─────────────────────────────────────────────────
@app.post("/api/optimize")
def api_optimize(req: ScheduleRequest, db: Session = Depends(get_db)):
    result = run_schedule(db, order_ids=req.order_ids)

    # Enrich batches with mold specs from ProductSpec
    for b_data in result["batches"]:
        ms_tuple = (b_data["mold_spec"]["od"], b_data["mold_spec"]["id"], b_data["mold_spec"]["length"])
        for m in b_data["molds"]:
            p = db.query(ProductSpec).filter(
                ProductSpec.voltage_kv == m["voltage_kv"],
                ProductSpec.current_a == m["current_a"],
            ).first()
            if p:
                m["mold_spec"] = {
                    "od": round(p.mold_od, 1),
                    "id": round(p.mold_id, 1),
                    "length": round(p.mold_length, 1),
                }
    return result


# ─── Batches ──────────────────────────────────────────────────
@app.get("/api/batches")
def api_batches(db: Session = Depends(get_db)):
    return [
        {
            "id": b.id,
            "batch_id": b.batch_id,
            "furnace": b.dryer_name,
            "furnace_spec": b.dryer_spec,
            "plan": b.plan_label,
            "mold_spec": {"od": b.mold_od, "id": b.mold_id, "length": b.mold_length},
            "total_molds": b.total_molds,
            "start_day": b.start_day,
            "end_day": b.end_day,
            "orders": json.loads(b.orders_json) if b.orders_json else [],
        }
        for b in db.query(Batch).order_by(Batch.batch_id).all()
    ]


@app.get("/api/batches/{batch_id}")
def api_batch_detail(batch_id: str, db: Session = Depends(get_db)):
    b = db.query(Batch).filter(Batch.batch_id == batch_id).first()
    if not b:
        raise HTTPException(404, "Batch not found")
    return {
        "id": b.id,
        "batch_id": b.batch_id,
        "furnace": b.dryer_name,
        "furnace_spec": b.dryer_spec,
        "plan": b.plan_label,
        "mold_spec": {"od": b.mold_od, "id": b.mold_id, "length": b.mold_length},
        "total_molds": b.total_molds,
        "start_day": b.start_day,
        "end_day": b.end_day,
        "start_date": b.start_date,
        "end_date": b.end_date,
        "orders": json.loads(b.orders_json) if b.orders_json else [],
    }


# ─── Export CSV ───────────────────────────────────────────────
@app.get("/api/export/csv")
def api_export_csv(db: Session = Depends(get_db)):
    batches = db.query(Batch).order_by(Batch.batch_id).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["批次", "乾燥罐", "方案", "模具外徑", "模具內徑", "模具長度", "訂單編號", "電壓kV", "電流A", "數量"])
    for b in batches:
        orders = json.loads(b.orders_json) if b.orders_json else []
        for m in orders:
            w.writerow([
                b.batch_id, b.dryer_name, b.plan_label,
                b.mold_od, b.mold_id, b.mold_length,
                m["order_id"], m["voltage_kv"], m["current_a"], m["qty"],
            ])
    out.seek(0)
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="排爐計劃_{datetime.now().strftime("%Y%m%d")}.csv"'},
    )


# ─── Health ───────────────────────────────────────────────────
@app.get("/healthz")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    print(f"DB: {DB_PATH}")
    print("Starting on http://localhost:5556")
    uvicorn.run("main:app", host="0.0.0.0", port=5556, reload=False)
