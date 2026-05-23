"""Validator unit tests — schedule validation + overdue check"""
from unittest.mock import MagicMock

from engine.validator import check_overdue, validate_schedule


class TestValidateSchedule:
    def test_empty_schedule(self):
        """Validator handles empty result gracefully."""
        result = {
            "summary": {"total_hours": 0, "scheduled": 0, "skipped": 0},
            "order_schedule": [],
            "kiln_schedule": {},
            "warnings": [],
        }
        report = validate_schedule(result)
        assert report["valid"] is True
        assert report["stats"]["total_scheduled"] == 0
        assert report["stats"]["total_skipped"] == 0

    def test_normal_schedule_no_capacity_issue(self):
        """Balanced schedule — no errors, no capacity warnings."""
        result = {
            "summary": {"total_hours": 5000, "scheduled": 50, "skipped": 0, "warnings": []},
            "order_schedule": [
                {"plan_no": "PO-001", "delivery_date": "2026-06-01", "mold_od": 300, "est_hours": 100},
                {"plan_no": "PO-002", "delivery_date": "2026-06-15", "mold_od": 350, "est_hours": 200},
            ],
            "kiln_schedule": {
                "K1": {"kiln_name": "Kiln 1", "hours_used": 2500, "total_slots": 4, "slots_used": 2},
                "K2": {"kiln_name": "Kiln 2", "hours_used": 2500, "total_slots": 4, "slots_used": 2},
            },
            "warnings": [],
        }
        report = validate_schedule(result)
        assert report["valid"] is True
        # estimated_days = 5000 / (1098 * 2) ≈ 2.3
        assert report["stats"]["estimated_days"] < 10
        assert "avg_kiln_hours" in report["stats"]

    def test_capacity_warning_above_60_days(self):
        """Large total_hours triggers warning."""
        result = {
            "summary": {"total_hours": 160000, "scheduled": 160, "skipped": 0, "warnings": []},
            "order_schedule": [
                {"plan_no": "PO-BIG", "delivery_date": "2026-07-01", "mold_od": 400, "est_hours": 800}
                for _ in range(20)
            ],
            "kiln_schedule": {
                "K1": {"kiln_name": "K1", "hours_used": 80000, "total_slots": 4, "slots_used": 4},
                "K2": {"kiln_name": "K2", "hours_used": 80000, "total_slots": 4, "slots_used": 4},
            },
            "warnings": [],
        }
        report = validate_schedule(result)
        # estimated_days = 200000 / (1098 * 2) ≈ 91 → should trigger warning
        assert len(report["warnings"]) >= 1

    def test_capacity_error_above_90_days(self):
        """Very large workload triggers error."""
        result = {
            "summary": {"total_hours": 250000, "scheduled": 250, "skipped": 0, "warnings": []},
            "order_schedule": [
                {"plan_no": f"PO-{i}", "delivery_date": "2026-08-01", "mold_od": 400, "est_hours": 1000}
                for i in range(25)
            ],
            "kiln_schedule": {
                "K1": {"kiln_name": "K1", "hours_used": 125000, "total_slots": 4, "slots_used": 4},
                "K2": {"kiln_name": "K2", "hours_used": 125000, "total_slots": 4, "slots_used": 4},
            },
            "warnings": [],
        }
        report = validate_schedule(result)
        assert report["valid"] is False
        assert len(report["errors"]) >= 1

    def test_unbalanced_load_warning(self):
        """Highly unbalanced kilns trigger load warning."""
        result = {
            "summary": {"total_hours": 12000, "scheduled": 12, "skipped": 0, "warnings": []},
            "order_schedule": [
                {"plan_no": f"PO-{i}", "delivery_date": "2026-06-01", "mold_od": 300, "est_hours": 1000}
                for i in range(12)
            ],
            "kiln_schedule": {
                "K1": {"kiln_name": "K1", "hours_used": 11000, "total_slots": 4, "slots_used": 4},
                "K2": {"kiln_name": "K2", "hours_used": 1000, "total_slots": 4, "slots_used": 1},
            },
            "warnings": [],
        }
        report = validate_schedule(result)
        # ratio 11000/1000 = 11 > 5 → warning
        assert any("負載不均" in w for w in report["warnings"])

    def test_out_of_order_delivery_dates(self):
        """Non-sorted delivery dates trigger warning."""
        result = {
            "summary": {"total_hours": 500, "scheduled": 3, "skipped": 0, "warnings": []},
            "order_schedule": [
                {"plan_no": "PO-LATE", "delivery_date": "2026-12-31", "mold_od": 300, "est_hours": 100},
                {"plan_no": "PO-EARLY", "delivery_date": "2026-01-01", "mold_od": 300, "est_hours": 100},
                {"plan_no": "PO-MID", "delivery_date": "2026-06-15", "mold_od": 300, "est_hours": 100},
            ],
            "kiln_schedule": {},
            "warnings": [],
        }
        report = validate_schedule(result)
        assert any("交期不完全一致" in w for w in report["warnings"])

    def test_preserves_existing_warnings(self):
        """Validator appends to existing warnings."""
        result = {
            "summary": {"total_hours": 500, "scheduled": 1, "skipped": 0},
            "order_schedule": [
                {"plan_no": "PO-001", "delivery_date": "2026-06-01", "mold_od": 300, "est_hours": 500},
            ],
            "kiln_schedule": {},
            "warnings": ["pre-existing warning"],
        }
        report = validate_schedule(result)
        assert "pre-existing warning" in report["warnings"]


class TestCheckOverdue:
    def test_no_overdue_orders(self):
        """Empty DB — no overdue orders."""
        mock_factory = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_factory.return_value = mock_session

        result = check_overdue(mock_factory)
        assert result["overdue_count"] == 0
        assert result["overdue_orders"] == []

    def test_overdue_orders_found(self):
        """Returns overdue order details."""
        from datetime import date

        mock_factory = MagicMock()
        mock_session = MagicMock()
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.plan_no = "OVERDUE-001"
        mock_order.contract_no = "C-OLD-001"
        mock_order.delivery_date = "2024-01-01"
        mock_session.query.return_value.filter.return_value.all.return_value = [mock_order]
        mock_factory.return_value = mock_session

        result = check_overdue(mock_factory)
        assert result["overdue_count"] == 1
        assert result["overdue_orders"][0]["plan_no"] == "OVERDUE-001"
        assert result["overdue_orders"][0]["delivery_date"] == "2024-01-01"
        mock_session.close.assert_called_once()
