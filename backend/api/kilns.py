"""Kilns API — 干燥罐 CRUD"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Kiln
from schemas import KilnCreate, KilnUpdate, KilnOut
from crud import (
    get_kiln, get_kiln_by_no, get_kilns, get_kilns_count,
    create_kiln, update_kiln, delete_kiln,
)

router = APIRouter(prefix="/api/v1/kilns", tags=["kilns"])


@router.get("/", response_model=list[KilnOut])
def list_kilns(db: Session = Depends(get_db)):
    kilns = get_kilns(db)
    result = []
    for k in kilns:
        schemes = json.loads(k.schemes_json) if k.schemes_json else {}
        result.append(KilnOut(
            id=k.id, kiln_no=k.kiln_no, name=k.name,
            inner_dia=k.inner_dia, height=k.height,
            schemes=schemes,
            created_at=k.created_at, updated_at=k.updated_at,
        ))
    return result


@router.get("/count")
def count_kilns(db: Session = Depends(get_db)):
    return {"count": get_kilns_count(db)}


@router.get("/{kiln_id}", response_model=KilnOut)
def get_kiln_detail(kiln_id: int, db: Session = Depends(get_db)):
    k = get_kiln(db, kiln_id)
    if not k:
        raise HTTPException(404, "干燥罐不存在")
    schemes = json.loads(k.schemes_json) if k.schemes_json else {}
    return KilnOut(
        id=k.id, kiln_no=k.kiln_no, name=k.name,
        inner_dia=k.inner_dia, height=k.height,
        schemes=schemes,
        created_at=k.created_at, updated_at=k.updated_at,
    )


@router.post("/", response_model=KilnOut, status_code=201)
def add_kiln(kiln: KilnCreate, db: Session = Depends(get_db)):
    existing = get_kiln_by_no(db, kiln.kiln_no)
    if existing:
        raise HTTPException(409, f"干燥罐 {kiln.kiln_no} 已存在")
    k = create_kiln(db, kiln)
    schemes = json.loads(k.schemes_json) if k.schemes_json else {}
    return KilnOut(
        id=k.id, kiln_no=k.kiln_no, name=k.name,
        inner_dia=k.inner_dia, height=k.height,
        schemes=schemes,
        created_at=k.created_at, updated_at=k.updated_at,
    )


@router.put("/{kiln_id}", response_model=KilnOut)
def modify_kiln(kiln_id: int, kiln: KilnUpdate, db: Session = Depends(get_db)):
    k = update_kiln(db, kiln_id, kiln)
    if not k:
        raise HTTPException(404, "干燥罐不存在")
    schemes = json.loads(k.schemes_json) if k.schemes_json else {}
    return KilnOut(
        id=k.id, kiln_no=k.kiln_no, name=k.name,
        inner_dia=k.inner_dia, height=k.height,
        schemes=schemes,
        created_at=k.created_at, updated_at=k.updated_at,
    )


@router.delete("/{kiln_id}")
def remove_kiln(kiln_id: int, db: Session = Depends(get_db)):
    ok = delete_kiln(db, kiln_id)
    if not ok:
        raise HTTPException(404, "干燥罐不存在")
    return {"deleted": True, "kiln_id": kiln_id}