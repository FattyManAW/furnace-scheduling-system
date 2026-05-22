"""Shared date utilities for furnace scheduling system"""
from datetime import datetime, timedelta

DEFAULT_DELIVERY_DAYS = 60


_EXCEL_EPOCH = datetime(1899, 12, 30)
_EXCEL_THRESHOLD = 10000


def excel_to_date(raw) -> str:
    """Convert Excel serial date (int/float/str) → ISO date string YYYY-MM-DD.

    Values ≤ _EXCEL_THRESHOLD that cannot be parsed as YYYY-MM-DD / YYYY/MM/DD /
    YYYYMMDD return the default (now + DEFAULT_DELIVERY_DAYS) to avoid polluting
    the DB with non-date strings like "0" or "9999".
    """
    _default = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
    if raw is None or raw == "":
        return _default
    if isinstance(raw, (int, float)):
        if raw > _EXCEL_THRESHOLD:
            return (_EXCEL_EPOCH + timedelta(days=int(raw))).strftime("%Y-%m-%d")
        # Values ≤ _EXCEL_THRESHOLD (including 0, negatives, 1-9999) are not valid Excel serially
        return _default
    s = str(raw).strip()
    # Try Excel serial first
    try:
        serial = float(s)
        if serial > _EXCEL_THRESHOLD:
            return (_EXCEL_EPOCH + timedelta(days=int(serial))).strftime("%Y-%m-%d")
        # String-converted values ≤ _EXCEL_THRESHOLD also invalid — fall through to date parsing
    except (ValueError, OverflowError):
        pass
    # Try standard date formats
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s[:10], fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return _default


def parse_delivery_date(raw):
    """Parse delivery_date to date object (for optimizer _dkey)"""
    _default = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
    if raw is None or raw == "":
        return _default
    if isinstance(raw, (int, float)):
        if raw > _EXCEL_THRESHOLD:
            return (_EXCEL_EPOCH + timedelta(days=int(raw))).date()
        return _default
    s = str(raw).strip()
    try:
        serial = float(s)
        if serial > _EXCEL_THRESHOLD:
            return (_EXCEL_EPOCH + timedelta(days=int(serial))).date()
        # Non-Excel numeric (≤threshold) → default
        return _default
    except (ValueError, OverflowError):
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except Exception:
            continue
    return _default
