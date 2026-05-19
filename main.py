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
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from database import init_db, make_get_db, Dryer, DryerPlan, MoldType, ProductSpec, ProcessStep, Order, Batch, Base
from engine import run_schedule
from optimizer import get_mold_for_product

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


# ═══════════════════════════════════════════════════════════════
#  Unified API Response
# ═══════════════════════════════════════════════════════════════

def ok(data=None, pagination: dict | None = None) -> dict:
    """Unified success response."""
    body = {"success": True, "data": data, "error": None}
    if pagination:
        body["pagination"] = pagination
    return body


def err(message: str, status: int = 400) -> dict:
    """Unified error response."""
    return {"success": False, "data": None, "error": {"message": message, "code": status}}


def paginate(query, page: int, page_size: int):
    """Apply pagination and return (items, pagination_meta)."""
    total = query.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, {"page": page, "page_size": page_size, "total": total, "total_pages": total_pages}


# ═══════════════════════════════════════════════════════════════
#  Global Exception Handler
# ═══════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=err(exc.detail, exc.status_code))


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    return JSONResponse(status_code=500, content=err(f"伺服器內部錯誤: {str(exc)}", 500))


# ═══════════════════════════════════════════════════════════════
#  Pydantic Schemas
# ═══════════════════════════════════════════════════════════════

class OrderCreate(BaseModel):
    order_id: str
    contract_no: str = ""
    voltage_kv: float
    current_a: float
    unit: str = "支"
    quantity: int
    delivery_date: str  # YYYY-MM-DD
    product_start: int = 0
    product_end: int = 0

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("數量必須大於 0")
        return v

    @field_validator("delivery_date")
    @classmethod
    def date_format(cls, v):
        from datetime import datetime as dt
        try:
            dt.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("交期格式必須為 YYYY-MM-DD")
        return v


class OrderUpdate(BaseModel):
    contract_no: Optional[str] = None
    voltage_kv: Optional[float] = None
    current_a: Optional[float] = None
    unit: Optional[str] = None
    quantity: Optional[int] = None
    delivery_date: Optional[str] = None
    product_start: Optional[int] = None
    product_end: Optional[int] = None
    is_selected: Optional[bool] = None

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("數量必須大於 0")
        return v


class OrderBulkSelect(BaseModel):
    order_ids: list[str]
    is_selected: bool


class MoldCreate(BaseModel):
    outer_diameter: float
    inner_diameter: float
    length: float
    quantity: int = 0
    is_active: bool = True

    @field_validator("quantity")
    @classmethod
    def qty_non_negative(cls, v):
        if v < 0:
            raise ValueError("庫存量不可為負")
        return v


class MoldUpdate(BaseModel):
    outer_diameter: Optional[float] = None
    inner_diameter: Optional[float] = None
    length: Optional[float] = None
    quantity: Optional[int] = None
    is_active: Optional[bool] = None


class DryerCreate(BaseModel):
    name: str
    inner_diameter: float
    height: float

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("乾燥罐名稱不可空白")
        return v.strip()


class DryerUpdate(BaseModel):
    inner_diameter: Optional[float] = None
    height: Optional[float] = None


class ProductCreate(BaseModel):
    voltage_kv: float
    current_a: float
    mold_od: float
    mold_id: float
    mold_length: float
    units_per_bundle: int = 1
    label: str = ""


class ProductUpdate(BaseModel):
    mold_od: Optional[float] = None
    mold_id: Optional[float] = None
    mold_length: Optional[float] = None
    units_per_bundle: Optional[int] = None
    label: Optional[str] = None


class PlanCreate(BaseModel):
    dryer_id: int
    plan_label: str
    upper_qty: int = 0
    upper_od: float = 0
    upper_id: float = 0
    upper_length: float = 0
    lower_qty: int = 0
    lower_od: float = 0
    lower_id: float = 0
    lower_length: float = 0


class ScheduleRequest(BaseModel):
    order_ids: Optional[list[str]] = None
    furnaces: Optional[list[str]] = None


class BatchUpdate(BaseModel):
    is_selected: bool


class MoldMatchRequest(BaseModel):
    voltage_kv: float
    current_a: float


# ─── Serialization helpers ─────────────────────────────────────

def _serialize_order(o: Order) -> dict:
    return {
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
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _serialize_mold(m: MoldType) -> dict:
    return {
        "id": m.id,
        "outer_diameter": m.outer_diameter,
        "inner_diameter": m.inner_diameter,
        "length": m.length,
        "quantity": m.quantity,
        "is_active": m.is_active,
    }


def _serialize_dryer(d: Dryer) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "inner_diameter": d.inner_diameter,
        "height": d.height,
        "plans": [
            {
                "id": p.id,
                "plan": p.plan_label,
                "upper": {"qty": p.upper_qty, "od": p.upper_od, "id": p.upper_id, "length": p.upper_length},
                "lower": {"qty": p.lower_qty, "od": p.lower_od, "id": p.lower_id, "length": p.lower_length},
            }
            for p in sorted(d.plans, key=lambda x: x.plan_label)
        ],
    }


def _serialize_product(p: ProductSpec) -> dict:
    return {
        "seq": p.id,
        "voltage_kv": p.voltage_kv,
        "current_a": p.current_a,
        "mold_od": p.mold_od,
        "mold_id": p.mold_id,
        "mold_length": p.mold_length,
        "units_per_bundle": p.units_per_bundle,
        "label": p.label,
    }


# ═══════════════════════════════════════════════════════════════
#  Static Files
# ═══════════════════════════════════════════════════════════════

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "index.html"))


# ═══════════════════════════════════════════════════════════════
#  Health
# ═══════════════════════════════════════════════════════════════

@app.get("/healthz")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ═══════════════════════════════════════════════════════════════
#  Summary
# ═══════════════════════════════════════════════════════════════

@app.get("/api/summary")
def api_summary(db: Session = Depends(get_db)):
    return ok({
        "dryers_count": db.query(Dryer).count(),
        "plans_count": db.query(DryerPlan).count(),
        "molds_count": db.query(MoldType).count(),
        "products_count": db.query(ProductSpec).count(),
        "orders_count": db.query(Order).count(),
        "batches_count": db.query(Batch).count(),
    })


# ═══════════════════════════════════════════════════════════════
#  Orders — CRUD
# ═══════════════════════════════════════════════════════════════

@app.get("/api/orders")
def api_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
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
    query = query.order_by(Order.delivery_date.asc())
    items, paging = paginate(query, page, page_size)
    return ok([_serialize_order(o) for o in items], paging)


@app.post("/api/orders")
def api_order_create(req: OrderCreate, db: Session = Depends(get_db)):
    if db.query(Order).filter(Order.order_id == req.order_id).first():
        raise HTTPException(409, f"訂單 {req.order_id} 已存在")
    o = Order(
        order_id=req.order_id,
        contract_no=req.contract_no,
        voltage_kv=req.voltage_kv,
        current_a=req.current_a,
        unit=req.unit,
        quantity=req.quantity,
        delivery_date=req.delivery_date,
        product_start=req.product_start,
        product_end=req.product_end,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return ok(_serialize_order(o))


@app.get("/api/orders/{order_id}")
def api_order_get(order_id: str, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.order_id == order_id).first()
    if not o:
        raise HTTPException(404, f"訂單 {order_id} 不存在")
    return ok(_serialize_order(o))


@app.put("/api/orders/{order_id}")
def api_order_update(order_id: str, req: OrderUpdate, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.order_id == order_id).first()
    if not o:
        raise HTTPException(404, f"訂單 {order_id} 不存在")
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(o, field, val)
    db.commit()
    db.refresh(o)
    return ok(_serialize_order(o))


@app.delete("/api/orders/{order_id}")
def api_order_delete(order_id: str, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.order_id == order_id).first()
    if not o:
        raise HTTPException(404, f"訂單 {order_id} 不存在")
    db.delete(o)
    db.commit()
    return ok({"deleted": order_id})


@app.post("/api/orders/bulk-select")
def api_order_bulk_select(req: OrderBulkSelect, db: Session = Depends(get_db)):
    updated = db.query(Order).filter(Order.order_id.in_(req.order_ids)).update(
        {"is_selected": req.is_selected}, synchronize_session="fetch"
    )
    db.commit()
    return ok({"updated_count": updated})


# ═══════════════════════════════════════════════════════════════
#  Molds — CRUD
# ═══════════════════════════════════════════════════════════════

@app.get("/api/molds")
def api_molds(db: Session = Depends(get_db)):
    return ok([
        _serialize_mold(m)
        for m in db.query(MoldType).order_by(MoldType.outer_diameter.desc()).all()
    ])


@app.post("/api/molds")
def api_mold_create(req: MoldCreate, db: Session = Depends(get_db)):
    existing = db.query(MoldType).filter(
        MoldType.outer_diameter == req.outer_diameter,
        MoldType.inner_diameter == req.inner_diameter,
        MoldType.length == req.length,
    ).first()
    if existing:
        raise HTTPException(409, f"模具 Φ{req.outer_diameter}/{req.inner_diameter}×{req.length} 已存在")
    m = MoldType(**req.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return ok(_serialize_mold(m))


@app.put("/api/molds/{mold_id}")
def api_mold_update(mold_id: int, req: MoldUpdate, db: Session = Depends(get_db)):
    m = db.query(MoldType).filter(MoldType.id == mold_id).first()
    if not m:
        raise HTTPException(404, f"模具 #{mold_id} 不存在")
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(m, field, val)
    db.commit()
    db.refresh(m)
    return ok(_serialize_mold(m))


@app.delete("/api/molds/{mold_id}")
def api_mold_delete(mold_id: int, db: Session = Depends(get_db)):
    m = db.query(MoldType).filter(MoldType.id == mold_id).first()
    if not m:
        raise HTTPException(404, f"模具 #{mold_id} 不存在")
    db.delete(m)
    db.commit()
    return ok({"deleted": mold_id})


# ═══════════════════════════════════════════════════════════════
#  Dryers (Furnaces) — CRUD
# ═══════════════════════════════════════════════════════════════

@app.get("/api/dryers")
def api_dryers(db: Session = Depends(get_db)):
    return ok([
        _serialize_dryer(d) for d in db.query(Dryer).order_by(Dryer.id).all()
    ])


@app.get("/api/dryers/{name}")
def api_dryer_detail(name: str, db: Session = Depends(get_db)):
    d = db.query(Dryer).filter(Dryer.name == name).first()
    if not d:
        raise HTTPException(404, f"乾燥罐 {name} 不存在")
    return ok(_serialize_dryer(d))


@app.post("/api/dryers")
def api_dryer_create(req: DryerCreate, db: Session = Depends(get_db)):
    if db.query(Dryer).filter(Dryer.name == req.name).first():
        raise HTTPException(409, f"乾燥罐 {req.name} 已存在")
    d = Dryer(name=req.name, inner_diameter=req.inner_diameter, height=req.height)
    db.add(d)
    db.commit()
    db.refresh(d)
    return ok(_serialize_dryer(d))


@app.put("/api/dryers/{dryer_id}")
def api_dryer_update(dryer_id: int, req: DryerUpdate, db: Session = Depends(get_db)):
    d = db.query(Dryer).filter(Dryer.id == dryer_id).first()
    if not d:
        raise HTTPException(404, f"乾燥罐 #{dryer_id} 不存在")
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(d, field, val)
    db.commit()
    db.refresh(d)
    return ok(_serialize_dryer(d))


@app.delete("/api/dryers/{dryer_id}")
def api_dryer_delete(dryer_id: int, db: Session = Depends(get_db)):
    d = db.query(Dryer).filter(Dryer.id == dryer_id).first()
    if not d:
        raise HTTPException(404, f"乾燥罐 #{dryer_id} 不存在")
    db.delete(d)
    db.commit()
    return ok({"deleted": dryer_id})


# ═══════════════════════════════════════════════════════════════
#  Dryer Plans — CRUD
# ═══════════════════════════════════════════════════════════════

@app.post("/api/dryers/{dryer_id}/plans")
def api_plan_create(dryer_id: int, req: PlanCreate, db: Session = Depends(get_db)):
    d = db.query(Dryer).filter(Dryer.id == dryer_id).first()
    if not d:
        raise HTTPException(404, f"乾燥罐 #{dryer_id} 不存在")
    if db.query(DryerPlan).filter(DryerPlan.dryer_id == dryer_id, DryerPlan.plan_label == req.plan_label).first():
        raise HTTPException(409, f"方案 {req.plan_label} 已存在於罐 #{dryer_id}")
    p = DryerPlan(dryer_id=dryer_id, **{k: v for k, v in req.model_dump().items() if k not in ("dryer_id",)})
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok({"id": p.id, "plan": p.plan_label})


@app.delete("/api/dryers/{dryer_id}/plans/{plan_label}")
def api_plan_delete(dryer_id: int, plan_label: str, db: Session = Depends(get_db)):
    p = db.query(DryerPlan).filter(DryerPlan.dryer_id == dryer_id, DryerPlan.plan_label == plan_label).first()
    if not p:
        raise HTTPException(404, f"方案 {plan_label} 不存在於罐 #{dryer_id}")
    db.delete(p)
    db.commit()
    return ok({"deleted": f"{dryer_id}/{plan_label}"})


# ═══════════════════════════════════════════════════════════════
#  Products — CRUD
# ═══════════════════════════════════════════════════════════════

@app.get("/api/products")
def api_products(db: Session = Depends(get_db)):
    return ok([_serialize_product(p) for p in db.query(ProductSpec).all()])


@app.get("/api/products/{label}")
def api_product_detail(label: str, db: Session = Depends(get_db)):
    p = db.query(ProductSpec).filter(ProductSpec.label == label).first()
    if not p:
        raise HTTPException(404, f"產品 {label} 不存在")
    return ok(_serialize_product(p))


@app.post("/api/products")
def api_product_create(req: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(ProductSpec).filter(
        ProductSpec.voltage_kv == req.voltage_kv,
        ProductSpec.current_a == req.current_a,
    ).first()
    if existing:
        raise HTTPException(409, f"產品 {req.voltage_kv}kV/{req.current_a}A 已存在")
    label = req.label or f"{req.voltage_kv}kV/{req.current_a}A"
    p = ProductSpec(**{**req.model_dump(), "label": label})
    db.add(p)
    db.commit()
    db.refresh(p)
    return ok(_serialize_product(p))


@app.put("/api/products/{product_id}")
def api_product_update(product_id: int, req: ProductUpdate, db: Session = Depends(get_db)):
    p = db.query(ProductSpec).filter(ProductSpec.id == product_id).first()
    if not p:
        raise HTTPException(404, f"產品 #{product_id} 不存在")
    for field, val in req.model_dump(exclude_unset=True).items():
        setattr(p, field, val)
    if not p.label:
        p.label = f"{p.voltage_kv}kV/{p.current_a}A"
    db.commit()
    db.refresh(p)
    return ok(_serialize_product(p))


@app.delete("/api/products/{product_id}")
def api_product_delete(product_id: int, db: Session = Depends(get_db)):
    p = db.query(ProductSpec).filter(ProductSpec.id == product_id).first()
    if not p:
        raise HTTPException(404, f"產品 #{product_id} 不存在")
    db.delete(p)
    db.commit()
    return ok({"deleted": product_id})


# ═══════════════════════════════════════════════════════════════
#  Mold Match
# ═══════════════════════════════════════════════════════════════

@app.post("/api/mold-match")
def api_mold_match(req: MoldMatchRequest, db: Session = Depends(get_db)):
    ms = get_mold_for_product(req.voltage_kv, req.current_a)
    if ms:
        return ok({"mold_spec": {"od": ms[0], "id": ms[1], "length": ms[2]}})
    return ok({"mold_spec": None})


# ═══════════════════════════════════════════════════════════════
#  Process Steps
# ═══════════════════════════════════════════════════════════════

@app.get("/api/process-steps")
def api_process_steps(db: Session = Depends(get_db)):
    return ok([
        {
            "id": s.id,
            "step": s.step_name,
            "flow": s.flow,
            "sub": s.sub_flow,
            "calc": s.calc_method,
            "per_voltage_h": json.loads(s.per_voltage_hours) if s.per_voltage_hours else {},
        }
        for s in db.query(ProcessStep).order_by(ProcessStep.sort_order).all()
    ])


# ═══════════════════════════════════════════════════════════════
#  Optimize
# ═══════════════════════════════════════════════════════════════

@app.post("/api/optimize")
def api_optimize(req: ScheduleRequest, db: Session = Depends(get_db)):
    result = run_schedule(db, order_ids=req.order_ids)
    for b_data in result["batches"]:
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


# ═══════════════════════════════════════════════════════════════
#  Batches
# ═══════════════════════════════════════════════════════════════

@app.get("/api/batches")
def api_batches(db: Session = Depends(get_db)):
    return ok([
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
    ])


@app.get("/api/batches/{batch_id}")
def api_batch_detail(batch_id: str, db: Session = Depends(get_db)):
    b = db.query(Batch).filter(Batch.batch_id == batch_id).first()
    if not b:
        raise HTTPException(404, f"批次 {batch_id} 不存在")
    return ok({
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
    })


# ═══════════════════════════════════════════════════════════════
#  Export CSV
# ═══════════════════════════════════════════════════════════════

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


if __name__ == "__main__":
    import uvicorn
    print(f"DB: {DB_PATH}")
    print("Starting on http://localhost:5556")
    uvicorn.run("main:app", host="0.0.0.0", port=5556, reload=False)