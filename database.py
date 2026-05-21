"""
oven_scheduler/database.py
SQLAlchemy models and database initialization.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Dryer(Base):
    __tablename__ = "dryers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    inner_diameter = Column(Float, nullable=False)   # mm
    height = Column(Float, nullable=False)           # mm
    plans = relationship("DryerPlan", back_populates="dryer", cascade="all, delete-orphan")


class DryerPlan(Base):
    __tablename__ = "dryer_plans"

    id = Column(Integer, primary_key=True, index=True)
    dryer_id = Column(Integer, ForeignKey("dryers.id"), nullable=False)
    plan_label = Column(String(10), nullable=False)  # A, B, C, ...
    upper_qty = Column(Integer, default=0)
    upper_od = Column(Float, default=0)
    upper_id = Column(Float, default=0)
    upper_length = Column(Float, default=0)
    lower_qty = Column(Integer, default=0)
    lower_od = Column(Float, default=0)
    lower_id = Column(Float, default=0)
    lower_length = Column(Float, default=0)
    dryer = relationship("Dryer", back_populates="plans")

    __table_args__ = (UniqueConstraint("dryer_id", "plan_label", name="uq_dryer_plan"),)


class MoldType(Base):
    __tablename__ = "mold_types"

    id = Column(Integer, primary_key=True, index=True)
    outer_diameter = Column(Float, nullable=False)
    inner_diameter = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)  # total in inventory
    is_active = Column(Boolean, default=True)


class ProductSpec(Base):
    __tablename__ = "product_specs"

    id = Column(Integer, primary_key=True, index=True)
    voltage_kv = Column(Float, nullable=False)
    current_a = Column(Float, nullable=False)
    mold_od = Column(Float, nullable=False)
    mold_id = Column(Float, nullable=False)
    mold_length = Column(Float, nullable=False)
    units_per_bundle = Column(Integer, default=1)
    label = Column(String(100))  # e.g. "72.5kV/2000A"

    __table_args__ = (UniqueConstraint("voltage_kv", "current_a", name="uq_product_spec"),)


class ProcessStep(Base):
    __tablename__ = "process_steps"

    id = Column(Integer, primary_key=True, index=True)
    step_name = Column(String(200), nullable=False)
    flow = Column(String(100))
    sub_flow = Column(String(100))
    calc_method = Column(String(50))
    # Per-voltage hours stored as JSON string: {"10": 2.0, "24": 2.0, ...}
    per_voltage_hours = Column(String(2000))
    sort_order = Column(Integer, default=0)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False)
    contract_no = Column(String(50))
    voltage_kv = Column(Float, nullable=False)
    current_a = Column(Float, nullable=False)
    unit = Column(String(20))
    quantity = Column(Integer, nullable=False)
    delivery_date = Column(String(20))  # ISO date string "YYYY-MM-DD"
    product_start = Column(Integer, default=0)
    product_end = Column(Integer, default=0)
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(20), unique=True, nullable=False)
    dryer_name = Column(String(50), nullable=False)
    dryer_spec = Column(String(100))
    plan_label = Column(String(10))
    mold_od = Column(Float)
    mold_id = Column(Float)
    mold_length = Column(Float)
    total_molds = Column(Integer, default=0)
    start_day = Column(Integer, default=0)
    end_day = Column(Integer, default=0)
    start_date = Column(String(50))
    end_date = Column(String(50))
    orders_json = Column(String(2000))  # JSON: [{"order_id":"25-018","qty":6,...}]
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db(engine):
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def make_get_db(engine):
    """Factory: return FastAPI Depends()-compatible get_db() bound to engine."""
    from sqlalchemy.orm import sessionmaker
    _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _get_db():
        db = _SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return _get_db
