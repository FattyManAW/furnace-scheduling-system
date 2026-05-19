"""Pydantic schemas"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# ── Order ──────────────────────────────────────────────────────────────────
class OrderBase(BaseModel):
    plan_no: str
    contract_no: Optional[str] = None
    voltage_kv: float
    current_a: float
    qty: int
    delivery_date: Optional[str] = None
    product_from: Optional[str] = None
    product_to: Optional[str] = None
    status: str = "pending"
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    contract_no: Optional[str] = None
    voltage_kv: Optional[float] = None
    current_a: Optional[float] = None
    qty: Optional[int] = None
    delivery_date: Optional[str] = None
    product_from: Optional[str] = None
    product_to: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderOut(OrderBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Mold ───────────────────────────────────────────────────────────────────
class MoldBase(BaseModel):
    mold_no: str
    outer_dia: float
    inner_dia: float
    length: float
    stock_qty: int = 0
    location: Optional[str] = None
    status: str = "available"
    notes: Optional[str] = None


class MoldCreate(MoldBase):
    pass


class MoldUpdate(BaseModel):
    outer_dia: Optional[float] = None
    inner_dia: Optional[float] = None
    length: Optional[float] = None
    stock_qty: Optional[int] = None
    location: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class MoldOut(MoldBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Kiln ───────────────────────────────────────────────────────────────────
class KilnBase(BaseModel):
    kiln_no: str = Field(..., min_length=1, description="干燥罐编号")
    name: str = Field(..., min_length=1, description="干燥罐名称")
    inner_dia: float = Field(..., gt=0, description="内径 mm")
    height: float = Field(..., gt=0, description="高度 mm")
    schemes: Dict[str, Any] = Field(default_factory=dict, description="方案配置")


class KilnCreate(KilnBase):
    pass


class KilnUpdate(BaseModel):
    name: Optional[str] = None
    inner_dia: Optional[float] = Field(default=None, gt=0)
    height: Optional[float] = Field(default=None, gt=0)
    schemes: Optional[Dict[str, Any]] = None


class KilnOut(KilnBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Schedule ───────────────────────────────────────────────────────────────
class ScheduleRequest(BaseModel):
    order_ids: Optional[List[int]] = Field(default=None, description="Order IDs to schedule; all if omitted")
    strategy: str = Field(default="deadline", description="deadline / fill / balance")


class ScheduleEntryOut(BaseModel):
    id: int
    kiln_id: int
    plan_no: str
    contract_no: Optional[str]
    voltage_kv: float
    current_a: float
    qty: int
    delivery_date: Optional[str]
    mold_od: float
    mold_len: float
    est_hours: float
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleResult(BaseModel):
    summary: Dict[str, Any]
    kiln_summary: List[Dict[str, Any]]
    schedule: List[ScheduleEntryOut]
    warnings: List[str] = []


# ── Dashboard ──────────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_orders: int
    pending_orders: int
    scheduled_orders: int
    completed_orders: int
    overdue_orders: int
    total_kilns: int
    active_kilns: int
    total_molds: int
    total_hours_scheduled: float
    daily_hour_cap: float


# ── Report ────────────────────────────────────────────────────────────────
class ReportFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    kiln_id: Optional[int] = None
