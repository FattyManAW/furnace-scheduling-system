"""Kilns API — 干燥罐完整 CRUD"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Kiln
from schemas import KilnCreate, KilnUpdate, KilnOut, PaginatedResponse
from crud import (
    get_kiln, get_kiln_by_no, get_kilns, get_kilns_count,
    create_kiln, update_kiln, delete_kiln,
)

router = APIRouter(prefix="/api/v1/kilns", tags=["kilns"])


def _kiln_to_out(k: Kiln) -> KilnOut:
    """Convert a Kiln ORM object to KilnOut schema."""
    schemes = json.loads(k.schemes_json) if k.schemes_json else {}
    return KilnOut(
        id=k.id, kiln_no=k.kiln_no, name=k.name,
        inner_dia=k.inner_dia, height=k.height,
        schemes=schemes,
        created_at=k.created_at, updated_at=k.updated_at,
    )


@router.get("/", response_model=PaginatedResponse[KilnOut])
def list_kilns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """列出所有干燥罐，支援分頁"""
    all_kilns = get_kilns(db)
    total = get_kilns_count(db)
    items = [_kiln_to_out(k) for k in all_kilns[skip:skip + limit]]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/count")
def count_kilns(db: Session = Depends(get_db)):
    return {"count": get_kilns_count(db)}


@router.get("/{kiln_id}", response_model=KilnOut)
def get_kiln_detail(kiln_id: int, db: Session = Depends(get_db)):
    k = get_kiln(db, kiln_id)
    if not k:
        raise HTTPException(404, "干燥罐不存在")
    return _kiln_to_out(k)


@router.post("/", response_model=KilnOut, status_code=201)
def add_kiln(kiln: KilnCreate, db: Session = Depends(get_db)):
    existing = get_kiln_by_no(db, kiln.kiln_no)
    if existing:
        raise HTTPException(409, f"干燥罐 {kiln.kiln_no} 已存在")
    return _kiln_to_out(create_kiln(db, kiln))


@router.put("/{kiln_id}", response_model=KilnOut)
def modify_kiln(kiln_id: int, kiln: KilnUpdate, db: Session = Depends(get_db)):
    k = update_kiln(db, kiln_id, kiln)
    if not k:
        raise HTTPException(404, "干燥罐不存在")
    return _kiln_to_out(k)


@router.delete("/{kiln_id}")
def remove_kiln(kiln_id: int, db: Session = Depends(get_db)):
    ok = delete_kiln(db, kiln_id)
    if not ok:
        raise HTTPException(404, "干燥罐不存在")
    return {"deleted": True, "kiln_id": kiln_id}
