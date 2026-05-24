"""Test fixtures — SQLite in-memory for FastAPI TestClient"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 1) Patch database module to use a temp-file DB BEFORE importing anything
#    (sqlite:///:memory: creates a NEW db per connection — useless for testing)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database as _db

# Use a shared temp file so all sessions share the same DB
_fd, _dbpath = tempfile.mkstemp(suffix=".db", prefix="furnace_test_")
os.close(_fd)
os.environ["FURNACE_DB_URL"] = f"sqlite:///{_dbpath}"

_inmem = create_engine(f"sqlite:///{_dbpath}", connect_args={"check_same_thread": False})
_db.engine = _inmem
_db.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_inmem)
_db.Base.metadata.create_all(bind=_inmem)

# 2) Now safe to import the app — its create_all uses our patched engine
import contextlib

import pytest

from database import get_db
from main import app


def pytest_sessionfinish(session):
    """Clean up temp DB file after all tests."""
    with contextlib.suppress(OSError):
        os.unlink(_dbpath)


@pytest.fixture(scope="function", autouse=True)
def _clean_db(db_session):
    """Clear all tables before each test."""
    from sqlalchemy import text
    # Turn off FK enforcement for SQLite to allow clean deletes
    db_session.execute(text("PRAGMA foreign_keys = OFF"))
    for table in reversed(_db.Base.metadata.sorted_tables):
        with contextlib.suppress(Exception):
            db_session.execute(table.delete())
    db_session.commit()
    db_session.execute(text("PRAGMA foreign_keys = ON"))


@pytest.fixture(scope="function")
def db_session():
    """Per-test session that rolls back after."""
    session = _db.SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient using in-memory DB."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()


@pytest.fixture
def sample_order(db_session):
    from models import Order
    order = Order(
        plan_no="TEST-001", contract_no="C-2026-001",
        voltage_kv=220.0, current_a=150.0, qty=10,
        delivery_date="2026-06-30",
        product_from="raw", product_to="finished", status="pending",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.fixture
def sample_mold(db_session):
    from models import Mold
    mold = Mold(
        mold_no="M-001", outer_dia=120.0, inner_dia=100.0, length=200.0,
        stock_qty=5, location="A區-3架", status="available",
    )
    db_session.add(mold)
    db_session.commit()
    db_session.refresh(mold)
    return mold
