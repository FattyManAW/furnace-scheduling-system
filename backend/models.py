"""SQLAlchemy ORM models"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    plan_no = Column(String(50), unique=True, index=True, nullable=False)
    contract_no = Column(String(50), index=True)
    voltage_kv = Column(Float, nullable=False)
    current_a = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    delivery_date = Column(String(20), index=True)
    product_from = Column(String(50))
    product_to = Column(String(50))
    status = Column(String(20), default="pending")  # pending / scheduled / completed
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Mold(Base):
    __tablename__ = "molds"

    id = Column(Integer, primary_key=True, index=True)
    mold_no = Column(String(50), unique=True, index=True)
    outer_dia = Column(Float, nullable=False)
    inner_dia = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    stock_qty = Column(Integer, default=0)
    location = Column(String(100))
    status = Column(String(20), default="available")  # available / in_use / maintenance
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Kiln(Base):
    __tablename__ = "kilns"

    id = Column(Integer, primary_key=True, index=True)
    kiln_no = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    inner_dia = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    schemes_json = Column(Text)  # JSON blob of schemes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    kiln_id = Column(Integer, index=True)
    order_id = Column(Integer, index=True)
    plan_no = Column(String(50), index=True)
    contract_no = Column(String(50))
    voltage_kv = Column(Float, nullable=False)
    current_a = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    delivery_date = Column(String(20), index=True)
    mold_od = Column(Float, nullable=False)
    mold_len = Column(Float, nullable=False)
    est_hours = Column(Float, default=0)
    status = Column(String(20), default="scheduled")
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Product(Base):
    """產品規格對照表 — 電壓等級 → 模具尺寸對應"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_no = Column(Integer, nullable=False)
    voltage_kv = Column(Float, nullable=False, index=True)
    current_a = Column(Float)
    mold_od = Column(Float, nullable=False)
    mold_id = Column(Float)
    mold_len = Column(Float, nullable=False)
    capacity = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id = Column(Integer, primary_key=True, index=True)
    step_no = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    department = Column(String(50))
    team = Column(String(50))
    process_type = Column(String(50))
    calc_basis = Column(String(20))
    h10 = Column(Float, default=0)
    h24 = Column(Float, default=0)
    h36 = Column(Float, default=0)
    h40 = Column(Float, default=0)
