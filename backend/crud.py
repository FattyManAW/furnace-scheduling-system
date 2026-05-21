"""CRUD operations"""
from __future__ import annotations

import json
from datetime import datetime

from models import Kiln, Mold, Order, ProcessStep, Product, ScheduleEntry
from schemas import (
    KilnCreate,
    KilnUpdate,
    MoldCreate,
    MoldUpdate,
    OrderCreate,
    OrderUpdate,
    ProcessStepCreate,
    ProcessStepUpdate,
)
from sqlalchemy.orm import Session


# ── Orders ─────────────────────────────────────────────────────────────────
def get_order(db: Session, order_id: int) -> Order | None:
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_plan_no(db: Session, plan_no: str) -> Order | None:
    return db.query(Order).filter(Order.plan_no == plan_no).first()


def get_orders(db: Session, skip: int = 0, limit: int = 100, status: str | None = None,
               search: str | None = None) -> list[Order]:
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if search:
        q = q.filter(
            (Order.plan_no.contains(search)) |
            (Order.contract_no.contains(search))
        )
    return q.order_by(Order.id.desc()).offset(skip).limit(limit).all()


def get_orders_count(db: Session, status: Optional[str] = None, search: Optional[str] = None) -> int:
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if search:
        q = q.filter(
            (Order.plan_no.contains(search)) |
            (Order.contract_no.contains(search))
        )
    return q.count()


def create_order(db: Session, order: OrderCreate) -> Order:
    db_order = Order(**order.model_dump())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order(db: Session, order_id: int, order_update: OrderUpdate) -> Order | None:
    db_order = get_order(db, order_id)
    if not db_order:
        return None
    update_data = order_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_order, key, value)
    db_order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_order)
    return db_order


def delete_order(db: Session, order_id: int) -> bool:
    db_order = get_order(db, order_id)
    if not db_order:
        return False
    db.delete(db_order)
    db.commit()
    return True


def bulk_create_orders(db: Session, orders_data: list[dict]) -> int:
    """Bulk insert orders from JSON data. Returns count of inserted."""
    count = 0
    for od in orders_data:
        po = str(od.get("plan_no", ""))
        if not po:
            continue
        existing = db.query(Order).filter(Order.plan_no == po).first()
        if existing:
            continue
        db_order = Order(
            plan_no=po,
            contract_no=str(od.get("contract_no", "") or ""),
            voltage_kv=float(od.get("voltage_kv", 0) or 0),
            current_a=float(od.get("current_a", 0) or 0),
            qty=int(float(od.get("qty", 0) or 0)),
            delivery_date=str(od.get("delivery_date", "") or ""),
            product_from=str(od.get("product_from", "") or ""),
            product_to=str(od.get("product_to", "") or ""),
            status="pending",
        )
        db.add(db_order)
        count += 1
    db.commit()
    return count


# ── Molds ──────────────────────────────────────────────────────────────────
def get_mold(db: Session, mold_id: int) -> Mold | None:
    return db.query(Mold).filter(Mold.id == mold_id).first()


def get_mold_by_no(db: Session, mold_no: str) -> Mold | None:
    return db.query(Mold).filter(Mold.mold_no == mold_no).first()


def get_molds(db: Session, skip: int = 0, limit: int = 100, low_stock: bool = False) -> list[Mold]:
    q = db.query(Mold)
    if low_stock:
        q = q.filter(Mold.stock_qty < 10)
    return q.order_by(Mold.id).offset(skip).limit(limit).all()


def get_molds_count(db: Session) -> int:
    return db.query(Mold).count()


def create_mold(db: Session, mold: MoldCreate) -> Mold:
    db_mold = Mold(**mold.model_dump())
    db.add(db_mold)
    db.commit()
    db.refresh(db_mold)
    return db_mold


def update_mold(db: Session, mold_id: int, mold_update: MoldUpdate) -> Mold | None:
    db_mold = get_mold(db, mold_id)
    if not db_mold:
        return None
    update_data = mold_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mold, key, value)
    db_mold.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_mold)
    return db_mold


def adjust_mold_stock(db: Session, mold_id: int, delta: int, reason: str = "adjust") -> Mold | None:
    db_mold = get_mold(db, mold_id)
    if not db_mold:
        return None
    db_mold.stock_qty = max(0, db_mold.stock_qty + delta)
    db_mold.notes = (db_mold.notes or "") + f"\n[{reason}] {delta:+d}"
    db_mold.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_mold)
    return db_mold


def delete_mold(db: Session, mold_id: int) -> bool:
    db_mold = get_mold(db, mold_id)
    if not db_mold:
        return False
    db.delete(db_mold)
    db.commit()
    return True


# ── Kilns ──────────────────────────────────────────────────────────────────
def get_kiln(db: Session, kiln_id: int) -> Kiln | None:
    return db.query(Kiln).filter(Kiln.id == kiln_id).first()


def get_kiln_by_no(db: Session, kiln_no: str) -> Kiln | None:
    return db.query(Kiln).filter(Kiln.kiln_no == kiln_no).first()


def get_kilns(db: Session) -> list[Kiln]:
    return db.query(Kiln).order_by(Kiln.kiln_no).all()


def get_kilns_count(db: Session) -> int:
    return db.query(Kiln).count()


# ── Products ───────────────────────────────────────────────────────────────
def get_products(db: Session) -> list[Product]:
    return db.query(Product).order_by(Product.voltage_kv).all()


def get_products_by_voltage(db: Session, voltage_kv: float) -> list[Product]:
    return db.query(Product).filter(Product.voltage_kv == voltage_kv).all()


def get_products_count(db: Session) -> int:
    return db.query(Product).count()


def create_kiln(db: Session, kiln: KilnCreate) -> Kiln:
    data = kiln.model_dump()
    schemes = data.pop("schemes", {})
    db_kiln = Kiln(schemes_json=json.dumps(schemes, ensure_ascii=False), **data)
    db.add(db_kiln)
    db.commit()
    db.refresh(db_kiln)
    return db_kiln


def update_kiln(db: Session, kiln_id: int, kiln_update: KilnUpdate) -> Kiln | None:
    db_kiln = get_kiln(db, kiln_id)
    if not db_kiln:
        return None
    update_data = kiln_update.model_dump(exclude_unset=True)
    if "schemes" in update_data:
        db_kiln.schemes_json = json.dumps(update_data.pop("schemes"), ensure_ascii=False)
    for key, value in update_data.items():
        setattr(db_kiln, key, value)
    db_kiln.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_kiln)
    return db_kiln


def delete_kiln(db: Session, kiln_id: int) -> bool:
    db_kiln = get_kiln(db, kiln_id)
    if not db_kiln:
        return False
    db.delete(db_kiln)
    db.commit()
    return True


# ── Schedule ───────────────────────────────────────────────────────────────
def create_schedule_entry(db: Session, entry: dict) -> ScheduleEntry:
    db_entry = ScheduleEntry(**entry)
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


def get_schedule_entries(db: Session, kiln_id: int | None = None) -> list[ScheduleEntry]:
    q = db.query(ScheduleEntry)
    if kiln_id:
        q = q.filter(ScheduleEntry.kiln_id == kiln_id)
    return q.all()


def clear_schedule(db: Session) -> int:
    """Remove all schedule entries. Returns deleted count."""
    cnt = db.query(ScheduleEntry).count()
    db.query(ScheduleEntry).delete()
    db.commit()
    return cnt


# ── Process Steps ─────────────────────────────────────────────────────────
def get_process_step(db: Session, step_id: int):
    return db.query(ProcessStep).filter(ProcessStep.id == step_id).first()


def get_process_steps(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    process_type: Optional[str] = None,
):
    q = db.query(ProcessStep)
    if department:
        q = q.filter(ProcessStep.department == department)
    if process_type:
        q = q.filter(ProcessStep.process_type == process_type)
    return q.order_by(ProcessStep.step_no).offset(skip).limit(limit).all()


def get_process_steps_count(
    db: Session,
    department: Optional[str] = None,
    process_type: Optional[str] = None,
) -> int:
    q = db.query(ProcessStep)
    if department:
        q = q.filter(ProcessStep.department == department)
    if process_type:
        q = q.filter(ProcessStep.process_type == process_type)
    return q.count()


def create_process_step(db: Session, step: ProcessStepCreate):
    db_step = ProcessStep(**step.model_dump())
    db.add(db_step)
    db.commit()
    db.refresh(db_step)
    return db_step


def update_process_step(
    db: Session, step_id: int, step_update: ProcessStepUpdate
):
    db_step = get_process_step(db, step_id)
    if not db_step:
        return None
    update_data = step_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_step, key, value)
    db.commit()
    db.refresh(db_step)
    return db_step


def delete_process_step(db: Session, step_id: int) -> bool:
    db_step = get_process_step(db, step_id)
    if not db_step:
        return False
    db.delete(db_step)
    db.commit()
    return True


def get_departments(db: Session):
    rows = (
        db.query(ProcessStep.department)
        .filter(ProcessStep.department.isnot(None))
        .distinct()
        .order_by(ProcessStep.department)
        .all()
    )
    return [r[0] for r in rows if r[0]]

