"""Tests for date_utils.py — cover all date conversion/parsing edge cases"""

from datetime import datetime, timedelta
from unittest.mock import patch

from date_utils import DEFAULT_DELIVERY_DAYS, _EXCEL_EPOCH, _EXCEL_THRESHOLD
from date_utils import excel_to_date, parse_delivery_date


# ── excel_to_date ────────────────────────────────────────────────────────


class TestExcelToDate:
    """Coverage target: all uncovered branches in excel_to_date()"""

    def test_none_input(self):
        """L20: raw=None → return default (now + 60 days)"""
        result = excel_to_date(None)
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_empty_string_input(self):
        """L20: raw='' → return default"""
        result = excel_to_date("")
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_int_above_threshold(self):
        """L22-23: int > _EXCEL_THRESHOLD → Excel serial date"""
        result = excel_to_date(50000)
        expected = (_EXCEL_EPOCH + timedelta(days=50000)).strftime("%Y-%m-%d")
        assert result == expected

    def test_int_below_threshold(self):
        """L24-25: int ≤ _EXCEL_THRESHOLD → return default"""
        result = excel_to_date(500)
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_int_zero(self):
        """L24-25: int=0 → return default"""
        result = excel_to_date(0)
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_int_negative(self):
        """L24-25: negative int → return default"""
        result = excel_to_date(-100)
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_int_at_threshold(self):
        """L24-25: int equal to _EXCEL_THRESHOLD → return default"""
        result = excel_to_date(_EXCEL_THRESHOLD)
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_float_above_threshold(self):
        """L22-23: float > _EXCEL_THRESHOLD → Excel serial date"""
        result = excel_to_date(50000.7)
        expected = (_EXCEL_EPOCH + timedelta(days=int(50000.7))).strftime("%Y-%m-%d")
        assert result == expected

    def test_float_below_threshold(self):
        """L24-25: float ≤ _EXCEL_THRESHOLD → return default"""
        result = excel_to_date(3.14)
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_string_excel_serial_above_threshold(self):
        """L28-31: string Excel serial > threshold → Excel date"""
        result = excel_to_date("50000")
        expected = (_EXCEL_EPOCH + timedelta(days=50000)).strftime("%Y-%m-%d")
        assert result == expected

    def test_string_excel_serial_below_threshold(self):
        """L33-41: string ≤ threshold → falls through to date parsing,
        then returns default since '100' is not a valid date format either"""
        result = excel_to_date("100")
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_non_numeric_string(self):
        """L33-34, 41: non-numeric string → except pass → format loop fails → default"""
        result = excel_to_date("not-a-date-at-all")
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_slash_date_format(self):
        """L35-38: YYYY/MM/DD format → ISO date"""
        result = excel_to_date("2026/08/15")
        assert result == "2026-08-15"

    def test_compact_date_format(self):
        """L35-38: YYYYMMDD format → ISO date"""
        result = excel_to_date("20260815")
        assert result == "2026-08-15"

    def test_iso_date_format(self):
        """L35-38: YYYY-MM-DD format → ISO date (already covered but sanity)"""
        result = excel_to_date("2026-12-25")
        assert result == "2026-12-25"

    def test_date_with_time_component(self):
        """L35-38: date with time component — only first 10 chars matter"""
        result = excel_to_date("2026-08-15T12:00:00")
        assert result == "2026-08-15"

    def test_unparseable_string(self):
        """L41: unparseable string → default"""
        result = excel_to_date("xyz-99-abc")
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected

    def test_overflow_error_string(self):
        """L33-34: string that causes OverflowError on float() → falls through → default"""
        result = excel_to_date("1e5000")  # huge number causes OverflowError
        expected = (datetime.now() + timedelta(days=DEFAULT_DELIVERY_DAYS)).strftime("%Y-%m-%d")
        assert result == expected


# ── parse_delivery_date ──────────────────────────────────────────────────


class TestParseDeliveryDate:
    """Coverage target: all uncovered branches in parse_delivery_date()"""

    def test_none_input(self):
        """L48: raw=None → return default date"""
        result = parse_delivery_date(None)
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_empty_string_input(self):
        """L48: raw='' → return default date"""
        result = parse_delivery_date("")
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_int_above_threshold(self):
        """L50-51: int > _EXCEL_THRESHOLD → Excel serial date object"""
        result = parse_delivery_date(50000)
        expected = (_EXCEL_EPOCH + timedelta(days=50000)).date()
        assert result == expected

    def test_int_below_threshold(self):
        """L52: int ≤ _EXCEL_THRESHOLD → default date"""
        result = parse_delivery_date(500)
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_int_zero(self):
        """L52: int=0 → default date"""
        result = parse_delivery_date(0)
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_int_negative(self):
        """L52: negative int → default date"""
        result = parse_delivery_date(-1)
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_float_above_threshold(self):
        """L50-51: float > threshold → Excel serial date (int cast)"""
        result = parse_delivery_date(50000.9)
        expected = (_EXCEL_EPOCH + timedelta(days=int(50000.9))).date()
        assert result == expected

    def test_float_below_threshold(self):
        """L52: float ≤ threshold → default"""
        result = parse_delivery_date(3.14)
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_string_excel_serial_above_threshold(self):
        """L55-57: string Excel serial > threshold → date object"""
        result = parse_delivery_date("50000")
        expected = (_EXCEL_EPOCH + timedelta(days=50000)).date()
        assert result == expected

    def test_string_excel_serial_below_threshold(self):
        """L59: string ≤ threshold → falls through → default"""
        result = parse_delivery_date("100")
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_non_numeric_string(self):
        """L60-61, 67: non-numeric → except → format loop fails → default"""
        result = parse_delivery_date("not-a-date")
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_slash_date_format(self):
        """L62-64: YYYY/MM/DD → date object"""
        result = parse_delivery_date("2026/08/15")
        expected = datetime(2026, 8, 15).date()
        assert result == expected

    def test_compact_date_format(self):
        """L62-64: YYYYMMDD → date object"""
        result = parse_delivery_date("20260815")
        expected = datetime(2026, 8, 15).date()
        assert result == expected

    def test_iso_date_format(self):
        """L62-64: YYYY-MM-DD → date object"""
        result = parse_delivery_date("2026-12-25")
        expected = datetime(2026, 12, 25).date()
        assert result == expected

    def test_unparseable_string(self):
        """L67: completely unparseable → default"""
        result = parse_delivery_date("xyz-99-abc")
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected

    def test_overflow_error_string(self):
        """L60-61: overflow error on float() → default"""
        result = parse_delivery_date("1e5000")
        expected = datetime.now().date() + timedelta(days=DEFAULT_DELIVERY_DAYS)
        assert result == expected