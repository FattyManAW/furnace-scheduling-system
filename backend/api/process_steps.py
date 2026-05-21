"""Process Steps API — 製程步驟 CRUD"""
from typing import Optional

from crud import (
    create_process_step,
    delete_process_step,
    get_departments,
    get_process_step,
    get_process_steps,
    get_process_steps_count,
    update_process_step,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas import (
    PaginatedResponse,
    ProcessStepCreate,
    ProcessStepOut,
    ProcessStepUpdate,
)
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(prefix="/api/v1/process-steps", tags=["process-steps"])


@router.get("/", response_model=PaginatedResponse[ProcessStepOut])
def list_process_steps(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: Optional[str] = None,
    process_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """列出所有製程步驟，支援分頁與篩選"""
    items = get_process_steps(
        db, skip=skip, limit=limit,
        department=department, process_type=process_type,
    )
    total = get_process_steps_count(
        db, department=department, process_type=process_type,
    )
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    """列出所有不同部門"""
    return {"departments": get_departments(db)}


@router.get("/count")
def count_process_steps(db: Session = Depends(get_db)):
    return {"count": get_process_steps_count(db)}


@router.get("/{step_id}", response_model=ProcessStepOut)
def get_process_step_detail(step_id: int, db: Session = Depends(get_db)):
    obj = get_process_step(db, step_id)
    if not obj:
        raise HTTPException(404, "製程步驟不存在")
    return obj


@router.post("/", response_model=ProcessStepOut, status_code=201)
def add_process_step(step: ProcessStepCreate, db: Session = Depends(get_db)):
    return create_process_step(db, step)


@router.put("/{step_id}", response_model=ProcessStepOut)
def modify_process_step(step_id: int, step: ProcessStepUpdate, db: Session = Depends(get_db)):
    obj = update_process_step(db, step_id, step)
    if not obj:
        raise HTTPException(404, "製程步驟不存在")
    return obj


@router.delete("/{step_id}")
def remove_process_step(step_id: int, db: Session = Depends(get_db)):
    ok = delete_process_step(db, step_id)
    if not ok:
        raise HTTPException(404, "製程步驟不存在")
    return {"deleted": True, "step_id": step_id}
