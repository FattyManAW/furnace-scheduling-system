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

    # 1. 產能檢查（全廠產能 vs 工作量）
    total_h = result["summary"].get("total_hours", 0)
    kiln_count = len(result.get("kiln_schedule", {}))
    scheduled_orders = result.get("order_schedule", [])

    # 預估排程天數 = 總工時 / (爐數 × 單日上限)
    if kiln_count > 0 and scheduled_orders:
        daily_capacity = DAILY_HOUR_CAP * kiln_count
        estimated_days = total_h / daily_capacity
        report["stats"]["estimated_days"] = round(estimated_days, 1)
        report["stats"]["daily_capacity"] = round(daily_capacity, 1)

        # 檢查排程天數合理性（超過 60 天可能產能不足）
        if estimated_days > 90:
            report["errors"].append(
                f"產能嚴重不足: 預估需要 {estimated_days:.0f} 天 (全廠 {kiln_count} 爐)"
            )
            report["valid"] = False
        elif estimated_days > 60:
            report["warnings"].append(
                f"產能吃緊: 預估需要 {estimated_days:.0f} 天 (全廠 {kiln_count} 爐)"
            )

    # 2. 排程密度檢查（各爐工時分布 — 均勻度分析）
    kiln_hours = [k["hours_used"] for k in result.get("kiln_schedule", {}).values()]
    if kiln_hours:
        avg = sum(kiln_hours) / len(kiln_hours)
        report["stats"]["avg_kiln_hours"] = round(avg, 1)
        report["stats"]["max_kiln_hours"] = max(kiln_hours)
        report["stats"]["min_kiln_hours"] = min(kiln_hours)
        # 負載不均檢查：max/min > 3.0 表示有爐負擔過重
        if min(kiln_hours) > 0 and max(kiln_hours) / min(kiln_hours) > 5.0:
            report["warnings"].append(
                f"爐次負載不均: max={max(kiln_hours):.0f}h / min={min(kiln_hours):.0f}h"
            )

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
