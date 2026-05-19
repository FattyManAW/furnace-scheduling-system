"""Pydantic schemas — 統一請求驗證與回應格式"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any, Generic, TypeVar


# ── Helpers ───────────────────────────────────────────────────────────────
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """統一分頁回應格式"""
    items: List[T]
    total: int
    skip: int
    limit: int


class ErrorDetail(BaseModel):
    detail: str
    type: str = "error"
    request_id: Optional[str] = None


# ── Order ──────────────────────────────────────────────────────────────────
class OrderBase(BaseModel):
    plan_no: str = Field(..., min_length=1, max_length=50, description="計劃單號")
    contract_no: Optional[str] = Field(default=None, max_length=50, description="合約編號")
    voltage_kv: float = Field(..., gt=0, le=1100, description="電壓 kV")
    current_a: float = Field(..., gt=0, le=5000, description="電流 A")
    qty: int = Field(..., ge=1, le=99999, description="數量")
    delivery_date: Optional[str] = Field(default=None, max_length=20, description="交期 YYYY-MM-DD")
    product_from: Optional[str] = Field(default=None, max_length=50, description="產品來源")
    product_to: Optional[str] = Field(default=None, max_length=50, description="產品去向")
    status: str = Field(default="pending", pattern=r"^(pending|scheduled|completed|cancelled)$")
    notes: Optional[str] = Field(default=None, max_length=500)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    contract_no: Optional[str] = Field(default=None, max_length=50)
    voltage_kv: Optional[float] = Field(default=None, gt=0, le=1100)
    current_a: Optional[float] = Field(default=None, gt=0, le=5000)
    qty: Optional[int] = Field(default=None, ge=1, le=99999)
    delivery_date: Optional[str] = Field(default=None, max_length=20)
    product_from: Optional[str] = Field(default=None, max_length=50)
    product_to: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, pattern=r"^(pending|scheduled|completed|cancelled)$")
    notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("delivery_date")
    @classmethod
    def check_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", v):
            raise ValueError(f"無效日期格式: {v}，請使用 YYYY-MM-DD")
        return v


class OrderOut(OrderBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator('delivery_date', mode='before')
    @classmethod
    def normalize_date(cls, v):
        """Normalize Excel serial dates to ISO format on output."""
        if v is not None and v != "":
            s = str(v).strip()
            if s:
                try:
                    serial = float(s)
                    if serial > 10000:
                        from date_utils import excel_to_date
                        return excel_to_date(v)
                except (ValueError, TypeError):
                    pass
        return v

    class Config:
        from_attributes = True


# ── Mold ───────────────────────────────────────────────────────────────────
class MoldBase(BaseModel):
    mold_no: str = Field(..., min_length=1, max_length=50, description="模具編號")
    outer_dia: float = Field(..., gt=0, le=2000, description="外徑 mm")
    inner_dia: float = Field(..., gt=0, le=2000, description="內徑 mm")
    length: float = Field(..., gt=0, le=10000, description="長度 mm")
    stock_qty: int = Field(default=0, ge=0, le=9999, description="庫存量")
    location: Optional[str] = Field(default=None, max_length=100, description="存放位置")
    status: str = Field(default="available", pattern=r"^(available|in_use|maintenance)$", description="狀態")
    notes: Optional[str] = Field(default=None, max_length=500)


class MoldCreate(MoldBase):
    pass


class MoldUpdate(BaseModel):
    outer_dia: Optional[float] = Field(default=None, gt=0, le=2000)
    inner_dia: Optional[float] = Field(default=None, gt=0, le=2000)
    length: Optional[float] = Field(default=None, gt=0, le=10000)
    stock_qty: Optional[int] = Field(default=None, ge=0, le=9999)
    location: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, pattern=r"^(available|in_use|maintenance)$")
    notes: Optional[str] = Field(default=None, max_length=500)


class MoldOut(MoldBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Kiln ───────────────────────────────────────────────────────────────────
class KilnBase(BaseModel):
    kiln_no: str = Field(..., min_length=1, max_length=20, description="干燥罐編號")
    name: str = Field(..., min_length=1, max_length=50, description="干燥罐名稱")
    inner_dia: float = Field(..., gt=0, le=5000, description="內徑 mm")
    height: float = Field(..., gt=0, le=20000, description="高度 mm")
    schemes: Dict[str, Any] = Field(default_factory=dict, description="方案配置")


class KilnCreate(KilnBase):
    pass


class KilnUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    inner_dia: Optional[float] = Field(default=None, gt=0, le=5000)
    height: Optional[float] = Field(default=None, gt=0, le=20000)
    schemes: Optional[Dict[str, Any]] = None


class KilnOut(KilnBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── ProcessStep ────────────────────────────────────────────────────────────
class ProcessStepBase(BaseModel):
    step_no: int = Field(..., ge=0, description="步驟編號")
    step_name: str = Field(..., min_length=1, max_length=100, description="步驟名稱")
    department: Optional[str] = Field(default=None, max_length=50, description="部門")
    team: Optional[str] = Field(default=None, max_length=50, description="團隊")
    process_type: Optional[str] = Field(default=None, max_length=50, description="製程類型")
    calc_basis: Optional[str] = Field(default=None, max_length=20, description="計算基準")
    h10: float = Field(default=0, ge=0, description="10kV 工時")
    h24: float = Field(default=0, ge=0, description="24kV 工時")
    h36: float = Field(default=0, ge=0, description="36kV 工時")
    h40: float = Field(default=0, ge=0, description="40kV 工時")


class ProcessStepCreate(ProcessStepBase):
    pass


class ProcessStepUpdate(BaseModel):
    step_no: Optional[int] = Field(default=None, ge=0)
    step_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    department: Optional[str] = Field(default=None, max_length=50)
    team: Optional[str] = Field(default=None, max_length=50)
    process_type: Optional[str] = Field(default=None, max_length=50)
    calc_basis: Optional[str] = Field(default=None, max_length=20)
    h10: Optional[float] = Field(default=None, ge=0)
    h24: Optional[float] = Field(default=None, ge=0)
    h36: Optional[float] = Field(default=None, ge=0)
    h40: Optional[float] = Field(default=None, ge=0)


class ProcessStepOut(ProcessStepBase):
    id: int

    class Config:
        from_attributes = True


# ── Schedule ───────────────────────────────────────────────────────────────
class ScheduleRequest(BaseModel):
    order_ids: Optional[List[int]] = Field(default=None, description="要排程的訂單 ID，不傳則全部")
    strategy: str = Field(
        default="deadline",
        pattern=r"^(deadline|fill|balance)$",
        description="排程策略: deadline=交期優先, fill=窯滿優先, balance=平衡"
    )


class ScheduleEntryOut(BaseModel):
    id: int
    kiln_id: int
    kiln_name: Optional[str] = None
    plan_no: str
    contract_no: Optional[str] = None
    voltage_kv: float
    current_a: float
    qty: int
    delivery_date: Optional[str] = None
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


# ── Report / Import ───────────────────────────────────────────────────────
class ReportFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    kiln_id: Optional[int] = None


class BulkImportResult(BaseModel):
    imported: int
    skipped: int
    errors: List[str] = []
