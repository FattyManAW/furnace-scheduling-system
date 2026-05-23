"""ERP Simulation Router — /erp/* endpoints"""

from datetime import datetime
from typing import Optional

from database import get_db
from erp_sim import repository as repo
from erp_sim.sync import sync_schedule_to_erp
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_serializer
from sqlalchemy.orm import Session

router = APIRouter(prefix="/erp", tags=["erp"])


# ── Request / Response Schemas ──────────────────────────────────────────

class OrderCreate(BaseModel):
    order_no: str
    product_spec: Optional[str] = ""
    quantity: int = 0
    priority: str = "normal"


class OrderResponse(BaseModel):
    id: int
    order_no: str
    product_spec: Optional[str]
    quantity: int
    priority: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_created_at(self, v: datetime) -> str:
        return v.isoformat()


class DeliveryCreate(BaseModel):
    scheduled_date: Optional[str] = None
    delivery_date: Optional[str] = None
    furnace_id: Optional[str] = None
    position: int = 0
    status: str = "scheduled"
    est_hours: float = 0.0
    quantity: int = 0
    notes: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    order_id: int
    order_no: Optional[str]
    scheduled_date: Optional[str]
    delivery_date: Optional[str]
    furnace_id: Optional[str]
    position: int
    status: str
    est_hours: float
    quantity: int
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("created_at")
    def serialize_created_at(self, v: datetime) -> str:
        return v.isoformat()


class SyncRequest(BaseModel):
    schedule_result: dict


class SyncResponse(BaseModel):
    synced: int
    skipped: int
    errors: int
    delivery_ids: list[int]
    sync_time: str


class ProductionStatusResponse(BaseModel):
    orders: dict
    deliveries: dict
    total_quantity: int
    generated_at: str


# ── Order Endpoints ─────────────────────────────────────────────────────

@router.post("/orders", response_model=OrderResponse)
def create_order(body: OrderCreate, db: Session = Depends(get_db)):
    existing = repo.get_order_by_no(db, body.order_no)
    if existing:
        raise HTTPException(status_code=400, detail=f"訂單 {body.order_no} 已存在")
    return repo.create_order(
        db,
        order_no=body.order_no,
        product_spec=body.product_spec,
        quantity=body.quantity,
        priority=body.priority,
    )


@router.get("/orders", response_model=list[OrderResponse])
def list_orders(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return repo.list_orders(db, status=status, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = repo.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    return order


# ── Delivery Endpoints ──────────────────────────────────────────────────

@router.post("/orders/{order_id}/delivery", response_model=DeliveryResponse)
def create_delivery_for_order(
    order_id: int,
    body: DeliveryCreate,
    db: Session = Depends(get_db),
):
    order = repo.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="訂單不存在")
    return repo.create_delivery(
        db,
        order_id=order_id,
        order_no=order.order_no,
        scheduled_date=body.scheduled_date,
        delivery_date=body.delivery_date,
        furnace_id=body.furnace_id,
        position=body.position,
        status=body.status,
        est_hours=body.est_hours,
        quantity=body.quantity or order.quantity,
        notes=body.notes,
    )


@router.get("/deliveries", response_model=list[DeliveryResponse])
def list_deliveries(
    order_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return repo.list_deliveries(db, order_id=order_id, status=status, skip=skip, limit=limit)


# ── Sync Endpoint ───────────────────────────────────────────────────────

@router.post("/sync-schedule", response_model=SyncResponse)
def sync_schedule(body: SyncRequest, db: Session = Depends(get_db)):
    result = sync_schedule_to_erp(db, body.schedule_result)
    return result


# ── Production Status ───────────────────────────────────────────────────

@router.get("/production-status", response_model=ProductionStatusResponse)
def production_status(db: Session = Depends(get_db)):
    return repo.get_production_summary(db)