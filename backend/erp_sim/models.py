"""ERP Simulation 資料模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class ErpOrder(Base):
    """虛擬 ERP 中的訂單記錄"""
    __tablename__ = "erp_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, index=True, nullable=False)
    product_spec = Column(String(200))
    quantity = Column(Integer, nullable=False, default=0)
    priority = Column(String(20), default="normal")  # normal / high / urgent
    status = Column(String(20), default="pending")  # pending / scheduled / in_production / completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ErpDelivery(Base):
    """虛擬 ERP 中的交期記錄"""
    __tablename__ = "erp_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True, nullable=False)
    order_no = Column(String(50), index=True)
    scheduled_date = Column(String(20))  # 排程預計日期
    delivery_date = Column(String(20))  # 實際交期（從 optimizer result 計算）
    furnace_id = Column(String(50))
    position = Column(Integer, default=0)
    status = Column(String(20), default="scheduled")  # scheduled / in_progress / delivered
    est_hours = Column(Float, default=0.0)
    quantity = Column(Integer, default=0)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
