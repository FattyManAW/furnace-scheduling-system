"""排程 → ERP 同步邏輯

排爐完成後將排程結果（optimizer output）同步到 ERP 模擬層，
自動建立 delivery records。
"""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from erp_sim.repository import create_delivery, get_order_by_no, update_order_status


def _compute_delivery_date(scheduled_date_str: str, est_hours: float) -> str:
    """根據排程日期與預估工時計算實際交期（真實日期，非 2099）

    假設每日工作 8 小時，從 scheduled_date 起算。
    """
    try:
        base = datetime.strptime(scheduled_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        base = date.today()

    if est_hours <= 0:
        return base.strftime("%Y-%m-%d")

    # 每日 8 工作小時 → 需天數
    work_days = max(1, int(est_hours / 8) + (1 if est_hours % 8 > 0 else 0))
    # 跳過週末（簡單版：直加天數，週末算+2額外天）
    current = base
    days_added = 0
    while days_added < work_days:
        current = current + timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            days_added += 1

    return current.strftime("%Y-%m-%d")


def sync_schedule_to_erp(
    db: Session,
    schedule_result: dict,
    today: Optional[date] = None,
) -> dict:
    """將排程結果同步到 ERP 模擬層

    Args:
        db: SQLAlchemy session
        schedule_result: optimizer.schedule_orders() 回傳的 dict
        today: 基準日期（預設為今天）

    Returns:
        sync 統計 dict
    """
    if today is None:
        today = date.today()

    order_schedule = schedule_result.get("order_schedule", [])
    synced = 0
    skipped = 0
    errors = 0
    delivery_ids = []

    for entry in order_schedule:
        plan_no = entry.get("plan_no", "")
        if not plan_no:
            skipped += 1
            continue

        # 查找或建立 ERP order（按 order_no = plan_no）
        erp_order = get_order_by_no(db, plan_no)
        if not erp_order:
            skipped += 1
            continue

        # 計算真實交期
        scheduled_date = entry.get("delivery_date", today.strftime("%Y-%m-%d"))
        est_hours = entry.get("est_hours", 0)
        real_delivery = _compute_delivery_date(scheduled_date, est_hours)

        try:
            delivery = create_delivery(
                db=db,
                order_id=erp_order.id,
                order_no=plan_no,
                scheduled_date=scheduled_date,
                delivery_date=real_delivery,
                furnace_id=entry.get("kiln_id", ""),
                position=entry.get("slot_idx", 0),
                status="scheduled",
                est_hours=est_hours,
                quantity=entry.get("qty", erp_order.quantity),
                notes=f"kiln: {entry.get('kiln_name', '')}",
            )
            delivery_ids.append(delivery.id)

            # 更新 ERP order 狀態
            update_order_status(db, erp_order.id, "scheduled")
            synced += 1
        except Exception:
            errors += 1

    return {
        "synced": synced,
        "skipped": skipped,
        "errors": errors,
        "delivery_ids": delivery_ids,
        "sync_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
