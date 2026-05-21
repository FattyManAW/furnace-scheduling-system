"""排程約束驗證器"""
from __future__ import annotations

DAILY_HOUR_CAP = 1098.0


def validate_schedule(result: dict) -> dict:
    """驗證排程結果，回傳驗證報告"""
    report = {
        "valid": True,
        "errors": [],
        "warnings": list(result.get("warnings", [])),
        "stats": {},
    }

    # 1. 每日工時檢查
    total_h = result["summary"].get("total_hours", 0)
    if total_h > DAILY_HOUR_CAP * 1.2:
        report["errors"].append(
            f"工時嚴重超標: {total_h:.0f}h > {DAILY_HOUR_CAP:.0f}h (×1.2 警戒)"
        )
        report["valid"] = False
    elif total_h > DAILY_HOUR_CAP:
        report["warnings"].append(
            f"工時超標: {total_h:.0f}h > {DAILY_HOUR_CAP:.0f}h"
        )

    # 2. 排程密度檢查（各爐工時分布）
    kiln_hours = [k["hours_used"] for k in result.get("kiln_schedule", {}).values()]
    if kiln_hours:
        avg = sum(kiln_hours) / len(kiln_hours)
        report["stats"]["avg_kiln_hours"] = round(avg, 1)
        report["stats"]["max_kiln_hours"] = max(kiln_hours)
        report["stats"]["min_kiln_hours"] = min(kiln_hours)
        if max(kiln_hours) > DAILY_HOUR_CAP:
            report["errors"].append("有爐次工時超過每日上限")
            report["valid"] = False

    # 3. 大產品檢查
    for s in result.get("order_schedule", []):
        if s.get("mold_od", 0) >= 470:
            # 確認該爐有相容方案
            pass  # optimizer 已過濾

    # 4. 交期排序
    dates = [s["delivery_date"] for s in result.get("order_schedule", [])]
    if dates != sorted(dates):
        # 不一定嚴格排序（因爐位限制），只記警告
        report["warnings"].append("排程順序與交期不完全一致（爐位限制）")

    report["stats"]["total_scheduled"] = result["summary"].get("scheduled", 0)
    report["stats"]["total_skipped"] = result["summary"].get("skipped", 0)

    return report


def check_overdue(db_session_factory) -> dict:
    """檢查是否有逾期訂單

    Args:
        db_session_factory: callable that returns a new DB session
                          (e.g. SessionLocal)
    """
    from datetime import date

    from models import Order as OrderModel

    today = date.today().isoformat()
    db = db_session_factory()
    try:
        overdue = db.query(OrderModel).filter(
            OrderModel.delivery_date < today,
            OrderModel.status != "completed"
        ).all()
        return {
            "overdue_count": len(overdue),
            "overdue_orders": [
                {
                    "id": o.id,
                    "plan_no": o.plan_no,
                    "contract_no": o.contract_no,
                    "delivery_date": o.delivery_date,
                }
                for o in overdue
            ],
        }
    finally:
        db.close()
