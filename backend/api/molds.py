"""Molds API — 模具完整 CRUD + 庫存調整"""
from crud import (
    adjust_mold_stock,
    create_mold,
    delete_mold,
    get_mold,
    get_molds,
    get_molds_count,
    update_mold,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from models import Mold
from schemas import MoldCreate, MoldOut, MoldUpdate, PaginatedResponse
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(prefix="/api/v1/molds", tags=["molds"])


@router.get("/", response_model=PaginatedResponse[MoldOut])
def list_molds(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    low_stock: bool = Query(False, description="只顯示低庫存"),
    db: Session = Depends(get_db),
):
    """列出模具，支援分頁與低庫存篩選"""
    items = get_molds(db, skip=skip, limit=limit, low_stock=low_stock)
    total = get_molds_count(db)
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/count")
def count_molds(db: Session = Depends(get_db)):
    return {"count": get_molds_count(db)}


@router.get("/{mold_id}", response_model=MoldOut)
def get_mold_detail(mold_id: int, db: Session = Depends(get_db)):
    obj = get_mold(db, mold_id)
    if not obj:
        raise HTTPException(404, "模具不存在")
    return obj


@router.post("/", response_model=MoldOut, status_code=201)
def add_mold(mold: MoldCreate, db: Session = Depends(get_db)):
    existing = db.query(Mold).filter(Mold.mold_no == mold.mold_no).first()
    if existing:
        raise HTTPException(400, f"模具編號 {mold.mold_no} 已存在")
    return create_mold(db, mold)


@router.put("/{mold_id}", response_model=MoldOut)
def modify_mold(mold_id: int, mold: MoldUpdate, db: Session = Depends(get_db)):
    obj = update_mold(db, mold_id, mold)
    if not obj:
        raise HTTPException(404, "模具不存在")
    return obj


@router.delete("/{mold_id}")
def remove_mold(mold_id: int, db: Session = Depends(get_db)):
    ok = delete_mold(db, mold_id)
    if not ok:
        raise HTTPException(404, "模具不存在")
    return {"deleted": True, "mold_id": mold_id}


@router.post("/{mold_id}/stock")
def adjust_stock(
    mold_id: int,
    delta: int = Query(..., description="正數=入庫，負數=出庫"),
    reason: str = Query("manual adjust", description="調整原因"),
    db: Session = Depends(get_db),
):
    obj = adjust_mold_stock(db, mold_id, delta, reason)
    if not obj:
        raise HTTPException(404, "模具不存在")
    return {
        "mold_id": mold_id,
        "mold_no": obj.mold_no,
        "new_stock_qty": obj.stock_qty,
        "delta": delta,
        "reason": reason,
    }
