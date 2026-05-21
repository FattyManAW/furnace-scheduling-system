"""Orders API — 訂單完整 CRUD"""
from typing import Optional

from crud import (
    bulk_create_orders,
    create_order,
    delete_order,
    get_order,
    get_orders,
    get_orders_count,
    update_order,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from models import Order
from schemas import (
    BulkImportResult,
    OrderCreate,
    OrderOut,
    OrderUpdate,
    PaginatedResponse,
)
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.get("/", response_model=PaginatedResponse[OrderOut])
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, pattern=r"^(pending|scheduled|completed|cancelled)$"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """列出訂單，支援分頁、狀態篩選、全文搜尋"""
    items = get_orders(db, skip=skip, limit=limit, status=status, search=search)
    total = get_orders_count(db, status=status, search=search)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/count")
def count_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return {"count": get_orders_count(db, status=status)}


@router.get("/{order_id}", response_model=OrderOut)
def get_order_detail(order_id: int, db: Session = Depends(get_db)):
    obj = get_order(db, order_id)
    if not obj:
        raise HTTPException(404, "訂單不存在")
    return obj


@router.post("/", response_model=OrderOut, status_code=201)
def add_order(order: OrderCreate, db: Session = Depends(get_db)):
    existing = db.query(Order).filter(Order.plan_no == order.plan_no).first()
    if existing:
        raise HTTPException(400, f"計劃單號 {order.plan_no} 已存在")
    return create_order(db, order)


@router.put("/{order_id}", response_model=OrderOut)
def modify_order(order_id: int, order: OrderUpdate, db: Session = Depends(get_db)):
    obj = update_order(db, order_id, order)
    if not obj:
        raise HTTPException(404, "訂單不存在")
    return obj


@router.delete("/{order_id}")
def remove_order(order_id: int, db: Session = Depends(get_db)):
    ok = delete_order(db, order_id)
    if not ok:
        raise HTTPException(404, "訂單不存在")
    return {"deleted": True, "order_id": order_id}


@router.post("/bulk-import", response_model=BulkImportResult)
def bulk_import_orders(orders_data: list[dict], db: Session = Depends(get_db)):
    count = bulk_create_orders(db, orders_data)
    return BulkImportResult(
        imported=count,
        skipped=len(orders_data) - count,
        errors=[],
    )
