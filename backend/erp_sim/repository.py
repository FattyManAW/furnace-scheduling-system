"""ERP Simulation Repository — SQLite CRUD"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from erp_sim.models import ErpDelivery, ErpOrder

# ── Order CRUD ──────────────────────────────────────────────────────────

def create_order(
    db: Session,
    order_no: str,
    product_spec: Optional[str] = None,
    quantity: int = 0,
    priority: str = "normal",
) -> ErpOrder:
    order = ErpOrder(
        order_no=order_no,
        product_spec=product_spec or "",
        quantity=quantity,
        priority=priority,
        status="pending",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int) -> Optional[ErpOrder]:
    return db.query(ErpOrder).filter(ErpOrder.id == order_id).first()


def get_order_by_no(db: Session, order_no: str) -> Optional[ErpOrder]:
    return db.query(ErpOrder).filter(ErpOrder.order_no == order_no).first()


def list_orders(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ErpOrder]:
    q = db.query(ErpOrder)
    if status:
        q = q.filter(ErpOrder.status == status)
    return q.order_by(ErpOrder.created_at.desc()).offset(skip).limit(limit).all()


def update_order_status(db: Session, order_id: int, status: str) -> Optional[ErpOrder]:
    order = get_order(db, order_id)
    if order:
        order.status = status
        db.commit()
        db.refresh(order)
    return order


# ── Delivery CRUD ───────────────────────────────────────────────────────

def create_delivery(
    db: Session,
    order_id: int,
    order_no: str = "",
    scheduled_date: Optional[str] = None,
    delivery_date: Optional[str] = None,
    furnace_id: Optional[str] = None,
    position: int = 0,
    status: str = "scheduled",
    est_hours: float = 0.0,
    quantity: int = 0,
    notes: Optional[str] = None,
) -> ErpDelivery:
    delivery = ErpDelivery(
        order_id=order_id,
        order_no=order_no,
        scheduled_date=scheduled_date or "",
        delivery_date=delivery_date or "",
        furnace_id=furnace_id or "",
        position=position,
        status=status,
        est_hours=est_hours,
        quantity=quantity,
        notes=notes or "",
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def list_deliveries(
    db: Session,
    order_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[ErpDelivery]:
    q = db.query(ErpDelivery)
    if order_id is not None:
        q = q.filter(ErpDelivery.order_id == order_id)
    if status:
        q = q.filter(ErpDelivery.status == status)
    return q.order_by(ErpDelivery.created_at.desc()).offset(skip).limit(limit).all()


def get_deliveries_by_order(db: Session, order_id: int) -> list[ErpDelivery]:
    return (
        db.query(ErpDelivery)
        .filter(ErpDelivery.order_id == order_id)
        .order_by(ErpDelivery.created_at.desc())
        .all()
    )


def update_delivery_status(db: Session, delivery_id: int, status: str) -> Optional[ErpDelivery]:
    delivery = db.query(ErpDelivery).filter(ErpDelivery.id == delivery_id).first()
    if delivery:
        delivery.status = status
        db.commit()
        db.refresh(delivery)
    return delivery


# ── Production Status ───────────────────────────────────────────────────

def get_production_summary(db: Session) -> dict:
    """回傳生產狀態摘要"""
    total_orders = db.query(ErpOrder).count()
    pending_orders = db.query(ErpOrder).filter(ErpOrder.status == "pending").count()
    scheduled_orders = db.query(ErpOrder).filter(ErpOrder.status == "scheduled").count()
    in_prod_orders = db.query(ErpOrder).filter(ErpOrder.status == "in_production").count()
    completed_orders = db.query(ErpOrder).filter(ErpOrder.status == "completed").count()

    total_deliveries = db.query(ErpDelivery).count()
    scheduled_deliveries = db.query(ErpDelivery).filter(ErpDelivery.status == "scheduled").count()
    in_progress_deliveries = db.query(ErpDelivery).filter(ErpDelivery.status == "in_progress").count()
    delivered_count = db.query(ErpDelivery).filter(ErpDelivery.status == "delivered").count()

    total_quantity = db.query(ErpOrder).with_entities(
        ErpOrder.quantity
    ).all()
    total_qty_sum = sum(q[0] for q in total_quantity) if total_quantity else 0

    return {
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "scheduled": scheduled_orders,
            "in_production": in_prod_orders,
            "completed": completed_orders,
        },
        "deliveries": {
            "total": total_deliveries,
            "scheduled": scheduled_deliveries,
            "in_progress": in_progress_deliveries,
            "delivered": delivered_count,
        },
        "total_quantity": total_qty_sum,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
