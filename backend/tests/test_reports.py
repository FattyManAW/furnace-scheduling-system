"""Reports API tests — dashboard, CSV exports, JSON export"""
from datetime import date


def _create_order(client, plan_no, **overrides):
    defaults = {
        "plan_no": plan_no,
        "voltage_kv": 220.0, "current_a": 100.0, "qty": 5,
        "delivery_date": "2026-08-01",
    }
    defaults.update(overrides)
    return client.post("/api/v1/orders/", json=defaults)


def _create_mold(client, mold_no, **overrides):
    defaults = {
        "mold_no": mold_no,
        "outer_dia": 150.0, "inner_dia": 120.0, "length": 300.0,
        "stock_qty": 10,
    }
    defaults.update(overrides)
    return client.post("/api/v1/molds/", json=defaults)


def _create_kiln(client, kiln_no, **overrides):
    defaults = {
        "kiln_no": kiln_no, "name": f"Kiln {kiln_no}",
        "inner_dia": 800.0, "height": 1200.0,
    }
    defaults.update(overrides)
    return client.post("/api/v1/kilns/", json=defaults)


class TestDashboard:
    def test_empty_dashboard(self, client):
        """Dashboard with no data — should return structure."""
        resp = client.get("/api/v1/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "orders" in data
        assert "kilns" in data
        assert "molds" in data
        assert "schedule" in data
        assert "generated_at" in data
        assert "daily_cap" in data["schedule"]

    def test_dashboard_with_data(self, client, db_session):
        """Dashboard with orders, kilns, molds, and schedule entries."""
        today_str = date.today().isoformat()

        # Create orders
        _create_order(client, "RPT-001", contract_no="C-ALPHA", qty=10, status="pending", delivery_date="2027-12-31")
        _create_order(client, "RPT-002", contract_no="C-ALPHA", qty=20, status="pending", delivery_date="2027-12-31")
        _create_order(client, "RPT-003", contract_no="C-BETA", qty=5, status="scheduled", delivery_date=today_str)
        _create_order(client, "RPT-004", contract_no="C-GAMMA", qty=3, status="completed", delivery_date="2026-01-01")
        # Overdue: delivery_date is in the past, not completed
        _create_order(client, "RPT-OVERDUE", contract_no="C-DELTA", qty=8, status="pending", delivery_date="2020-01-01")

        # Create kilns
        _create_kiln(client, "K-RPT-001")
        _create_kiln(client, "K-RPT-002")

        # Create mold
        _create_mold(client, "M-RPT-001")

        # Create schedule entries with today's date (via direct DB insert for est_hours)
        from models import Order, ScheduleEntry
        # Get the scheduled order id
        orders = db_session.query(Order).all()
        sched_order = [o for o in orders if o.plan_no == "RPT-003"][0]

        entry = ScheduleEntry(
            kiln_id=1, order_id=sched_order.id,
            plan_no="RPT-003", contract_no="C-BETA",
            voltage_kv=220.0, current_a=100.0, qty=5,
            delivery_date=today_str,
            mold_od=150.0, mold_len=300.0, est_hours=8.0, status="scheduled",
        )
        db_session.add(entry)
        db_session.commit()

        resp = client.get("/api/v1/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        # Orders
        assert data["orders"]["total"] >= 5
        assert data["orders"]["pending"] >= 1
        assert data["orders"]["scheduled"] >= 1
        assert data["orders"]["completed"] >= 1
        assert data["orders"]["overdue"] >= 1
        assert len(data["overdue_orders"]) >= 1
        overdue_plan_nos = [o["plan_no"] for o in data["overdue_orders"]]
        assert "RPT-OVERDUE" in overdue_plan_nos

        # Pending by contract
        by_contract = {c["contract"]: c for c in data["orders"]["pending_by_contract"]}
        assert "C-ALPHA" in by_contract
        assert by_contract["C-ALPHA"]["count"] >= 2
        assert by_contract["C-ALPHA"]["qty"] >= 30
        assert "C-DELTA" in by_contract

        # Kilns
        assert data["kilns"]["total"] >= 2
        assert data["kilns"]["active_today"] >= 1

        # Molds
        assert data["molds"]["total"] >= 1

        # Schedule
        assert data["schedule"]["total_hours"] >= 8.0
        assert data["schedule"]["today_entries"] >= 1

    def test_dashboard_overdue_detail(self, client):
        """Overdue orders detail should be ordered by delivery_date."""
        _create_order(client, "OVD-001", contract_no="C-OLD", qty=3, status="pending", delivery_date="2020-01-01")
        _create_order(client, "OVD-002", contract_no="C-OLDER", qty=5, status="pending", delivery_date="2019-06-15")

        resp = client.get("/api/v1/reports/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        overdue = data["overdue_orders"]
        # Filter to only our test overdue orders
        our_overdue = [o for o in overdue if o["plan_no"] in ("OVD-001", "OVD-002")]
        assert len(our_overdue) == 2
        # Should be ordered by delivery_date ascending
        assert our_overdue[0]["delivery_date"] <= our_overdue[1]["delivery_date"]


class TestExportCSV:
    def test_export_orders_csv_empty(self, client):
        resp = client.get("/api/v1/reports/orders/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        # Header row + optional data
        lines = resp.text.strip().split("\r\n")
        assert len(lines) >= 1  # at least header

    def test_export_orders_csv_with_data(self, client):
        _create_order(client, "CSV-001", contract_no="C-CSV1", qty=12, delivery_date="2026-09-01", status="pending")

        resp = client.get("/api/v1/reports/orders/csv")
        assert resp.status_code == 200
        lines = resp.text.strip().split("\r\n")
        assert len(lines) >= 2  # header + at least 1 data row
        assert "CSV-001" in resp.text
        assert "C-CSV1" in resp.text

    def test_export_orders_csv_filtered(self, client):
        _create_order(client, "CSV-PENDING", qty=1, status="pending")
        _create_order(client, "CSV-DONE", qty=1, status="completed")

        resp = client.get("/api/v1/reports/orders/csv?status=pending")
        assert resp.status_code == 200
        # CSV should contain only pending orders
        assert "CSV-PENDING" in resp.text
        assert "CSV-DONE" not in resp.text

    def test_export_schedule_csv_empty(self, client):
        resp = client.get("/api/v1/reports/schedule/csv")
        assert resp.status_code == 200
        lines = resp.text.strip().split("\r\n")
        assert len(lines) >= 1  # at least header

    def test_export_schedule_csv_with_data(self, client, db_session):
        from models import Order, ScheduleEntry
        _create_order(client, "SCH-CSV-001", contract_no="C-SCH1", voltage_kv=220.0, current_a=100.0, qty=7, status="scheduled")
        o = db_session.query(Order).filter(Order.plan_no == "SCH-CSV-001").first()
        entry = ScheduleEntry(
            kiln_id=1, order_id=o.id,
            plan_no="SCH-CSV-001", contract_no="C-SCH1",
            voltage_kv=220.0, current_a=100.0, qty=7,
            delivery_date="2026-08-01",
            mold_od=150.0, mold_len=300.0, est_hours=12.5, status="scheduled",
        )
        db_session.add(entry)
        db_session.commit()

        resp = client.get("/api/v1/reports/schedule/csv")
        assert resp.status_code == 200
        assert "SCH-CSV-001" in resp.text


class TestExportJSON:
    def test_export_orders_json_empty(self, client):
        resp = client.get("/api/v1/reports/orders/json")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["orders"], list)
        assert "exported_at" in data

    def test_export_orders_json_with_data(self, client):
        _create_order(client, "JSON-001", contract_no="C-JSON1", voltage_kv=380.0, current_a=200.0,
                      qty=15, delivery_date="2026-10-01", status="pending",
                      product_from="raw", product_to="finished")

        resp = client.get("/api/v1/reports/orders/json")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["orders"]) >= 1
        our_order = next((o for o in data["orders"] if o["plan_no"] == "JSON-001"), None)
        assert our_order is not None
        assert our_order["voltage_kv"] == 380.0
        assert our_order["current_a"] == 200.0
        assert our_order["qty"] == 15
        assert our_order["status"] == "pending"
