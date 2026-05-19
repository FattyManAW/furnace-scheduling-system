"""Shared date utilities for furnace scheduling system"""
from datetime import datetime, timedelta

DEFAULT_DELIVERY_DAYS = 60


def excel_to_date(raw) -> str:
    """Convert Excel serial date (int/float/str) → ISO date string YYYY-MM-DD"""
    if raw is None or raw == "":
        return (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
    if isinstance(raw, (int, float)):
        if raw > 10000:
            return (datetime(1899, 12, 30) + timedelta(days=int(raw))).strftime("%Y-%m-%d")
        return str(raw)
    s = str(raw).strip()
    try:
        serial = float(s)
        if serial > 10000:
            return (datetime(1899, 12, 30) + timedelta(days=int(serial))).strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return s


def parse_delivery_date(raw):
    """Parse delivery_date to date object (for optimizer _dkey)"""
    if raw is None or raw == "":
        return datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
    if isinstance(raw, (int, float)):
        if raw > 10000:
            return (datetime(1899, 12, 30) + timedelta(days=int(raw))).date()
        return datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
    s = str(raw).strip()
    try:
        serial = float(s)
        if serial > 10000:
            return (datetime(1899, 12, 30) + timedelta(days=int(serial))).date()
    except (ValueError, OverflowError):
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except Exception:
            continue
    return datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)