"""Unit tests for ORM models"""

import pytest
from models import Kiln, Mold, Order, ProcessStep, ScheduleEntry


class TestOrderModel:
    def test_create_order(self, db_session):
        order = Order(plan_no="P-001", voltage_kv=220.0, current_a=150.0, qty=5)
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        assert order.id is not None
        assert order.plan_no == "P-001"
        assert order.created_at is not None

    def test_order_defaults(self, db_session):
        order = Order(plan_no="P-002", voltage_kv=110.0, current_a=80.0, qty=3)
        db_session.add(order)
        db_session.commit()
        assert order.status == "pending"
        assert order.contract_no is None
        assert order.created_at is not None

    def test_unique_plan_no(self, db_session):
        o1 = Order(plan_no="DUP-001", voltage_kv=220.0, current_a=100.0, qty=5)
        o2 = Order(plan_no="DUP-001", voltage_kv=110.0, current_a=50.0, qty=3)
        db_session.add(o1)
        db_session.commit()
        db_session.add(o2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_order_updated_at_changes(self, db_session):
        order = Order(plan_no="P-003", voltage_kv=220.0, current_a=100.0, qty=5)
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        ts1 = order.updated_at
        order.status = "scheduled"
        db_session.commit()
        db_session.refresh(order)
        assert order.updated_at != ts1


class TestMoldModel:
    def test_create_mold(self, db_session):
        mold = Mold(mold_no="M-100", outer_dia=150.0, inner_dia=120.0, length=300.0)
        db_session.add(mold)
        db_session.commit()
        db_session.refresh(mold)
        assert mold.id is not None
        assert mold.status == "available"
        assert mold.stock_qty == 0

    def test_mold_stock_default(self, db_session):
        mold = Mold(mold_no="M-101", outer_dia=100.0, inner_dia=80.0, length=250.0)
        db_session.add(mold)
        db_session.commit()
        assert mold.stock_qty == 0

    def test_unique_mold_no(self, db_session):
        db_session.add(Mold(mold_no="M-DUP", outer_dia=100.0, inner_dia=80.0, length=200.0))
        db_session.commit()
        db_session.add(Mold(mold_no="M-DUP", outer_dia=110.0, inner_dia=85.0, length=210.0))
        with pytest.raises(Exception):
            db_session.commit()


class TestKilnModel:
    def test_create_kiln(self, db_session):
        kiln = Kiln(kiln_no="K-01", name="干燥罐一号", inner_dia=500.0, height=1200.0)
        db_session.add(kiln)
        db_session.commit()
        db_session.refresh(kiln)
        assert kiln.id is not None
        assert kiln.name == "干燥罐一号"

    def test_kiln_schemes_json_null(self, db_session):
        kiln = Kiln(kiln_no="K-02", name="罐二", inner_dia=400.0, height=1000.0)
        db_session.add(kiln)
        db_session.commit()
        assert kiln.schemes_json is None

    def test_unique_kiln_no(self, db_session):
        db_session.add(Kiln(kiln_no="K-DUP", name="罐A", inner_dia=400.0, height=1000.0))
        db_session.commit()
        db_session.add(Kiln(kiln_no="K-DUP", name="罐B", inner_dia=400.0, height=1000.0))
        with pytest.raises(Exception):
            db_session.commit()


class TestScheduleEntryModel:
    def test_create_schedule_entry(self, db_session):
        entry = ScheduleEntry(
            plan_no="SCH-001",
            kiln_id=1,
            order_id=1,
            voltage_kv=220.0,
            current_a=150.0,
            qty=5,
            mold_od=120.0,
            mold_len=200.0,
        )
        db_session.add(entry)
        db_session.commit()
        db_session.refresh(entry)
        assert entry.id is not None
        assert entry.status == "scheduled"
        assert entry.est_hours == 0.0

    def test_schedule_entry_delivery_date(self, db_session):
        entry = ScheduleEntry(
            plan_no="SCH-002",
            kiln_id=2,
            order_id=2,
            voltage_kv=110.0,
            current_a=80.0,
            qty=3,
            mold_od=100.0,
            mold_len=150.0,
            delivery_date="2026-07-15",
        )
        db_session.add(entry)
        db_session.commit()
        assert entry.delivery_date == "2026-07-15"


class TestProcessStepModel:
    def test_create_process_step(self, db_session):
        step = ProcessStep(step_no=1, step_name="混合", department="成型", process_type="manual")
        db_session.add(step)
        db_session.commit()
        db_session.refresh(step)
        assert step.id is not None
        assert step.step_name == "混合"
        assert step.h10 == 0.0

    def test_process_step_hours(self, db_session):
        step = ProcessStep(step_no=2, step_name="干燥", h10=2.5, h24=6.0, h36=9.0)
        db_session.add(step)
        db_session.commit()
        assert step.h10 == 2.5
        assert step.h24 == 6.0
