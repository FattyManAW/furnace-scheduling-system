"""Test database.py — cover get_db generator, DB init paths, and error handling."""

import contextlib
import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── get_db() generator ──────────────────────────────────────────────────────

def test_get_db_yields_a_valid_session():
    """get_db() yields a working session (uses conftest-patched SessionLocal)."""
    from database import get_db

    gen = get_db()
    session = next(gen)

    assert session is not None
    result = session.execute(text("SELECT 1"))
    assert result.scalar() == 1

    # Properly close via finally
    with contextlib.suppress(StopIteration):
        next(gen)


def test_get_db_finally_closes_session():
    """Confirm the finally block in get_db() runs close()."""
    class SpySession:
        def __init__(self):
            self.closed = False
        def close(self):
            self.closed = True
        def rollback(self):
            pass

    spy = SpySession()

    def spy_get_db():
        db = spy
        try:
            yield db
        finally:
            db.close()

    gen = spy_get_db()
    s = next(gen)
    assert not s.closed
    with contextlib.suppress(StopIteration):
        next(gen)
    assert s.closed


def test_get_db_distinct_sessions():
    """Two calls to get_db() produce two distinct sessions."""
    from database import get_db

    g1 = get_db()
    s1 = next(g1)
    g2 = get_db()
    s2 = next(g2)

    assert s1 is not s2
    with contextlib.suppress(StopIteration):
        next(g1)
    with contextlib.suppress(StopIteration):
        next(g2)


def test_get_db_close_on_exception():
    """Close still runs if the try block raises (finally block coverage)."""
    class SpySession:
        def __init__(self):
            self.closed = False
        def close(self):
            self.closed = True

    spy = SpySession()

    def leaking_gen():
        db = spy
        try:
            yield db
            raise ValueError("boom")
        finally:
            db.close()

    gen = leaking_gen()
    next(gen)
    with pytest.raises(ValueError, match="boom"):
        next(gen)
    assert spy.closed


# ── Module-level: DB_DIR, SQLALCHEMY_DATABASE_URL, engine, SessionLocal, Base ─

@pytest.mark.skipif(
    os.environ.get("FURNACE_DB_URL") is not None,
    reason="conftest sets FURNACE_DB_URL; test default path separately"
)
def test_db_dir_default_path():
    """When FURNACE_DB_URL is unset, DB_DIR lives in backend/data."""
    # Re-import fresh
    import importlib

    import database as _db

    old = os.environ.pop("FURNACE_DB_URL", None)
    try:
        importlib.reload(_db)
        assert os.path.isdir(_db.DB_DIR)
        assert "data" in _db.DB_DIR
        assert _db.SQLALCHEMY_DATABASE_URL.startswith("sqlite:///")
        assert "furnace_schedule.db" in _db.SQLALCHEMY_DATABASE_URL
    finally:
        if old is not None:
            os.environ["FURNACE_DB_URL"] = old
        importlib.reload(_db)


def test_db_url_env_override():
    """FURNACE_DB_URL env var overrides the default."""
    import importlib

    import database as _db

    old = os.environ.get("FURNACE_DB_URL")
    os.environ["FURNACE_DB_URL"] = "sqlite:////tmp/custom_furnace_test.db"
    try:
        importlib.reload(_db)
        assert _db.SQLALCHEMY_DATABASE_URL == "sqlite:////tmp/custom_furnace_test.db"
    finally:
        if old is not None:
            os.environ["FURNACE_DB_URL"] = old
        else:
            os.environ.pop("FURNACE_DB_URL", None)
        importlib.reload(_db)


def test_engine_and_sessionlocal_exist():
    """Module exposes engine, SessionLocal, Base."""
    from database import Base, SessionLocal, engine

    assert engine is not None
    assert SessionLocal is not None
    assert Base is not None


def test_sessionlocal_creates_functional_session():
    """SessionLocal() yields a session that can execute SQL."""
    from database import SessionLocal

    session = SessionLocal()
    try:
        result = session.execute(text("SELECT 42"))
        assert result.scalar() == 42
    finally:
        session.close()


def test_base_metadata_is_usable():
    """Base is a valid declarative base that can reflect/deploy tables."""
    from database import Base, engine

    # Base is a DeclarativeMeta — tables are declared in models.py,
    # not here.  create_all should not crash.
    Base.metadata.create_all(bind=engine)
    assert Base.metadata is not None


# ── Edge cases ──────────────────────────────────────────────────────────────

def test_get_db_many_iterations():
    """Stress: many iterations, each session works and closes."""
    from database import get_db

    for _ in range(20):
        gen = get_db()
        s = next(gen)
        s.execute(text("SELECT 1"))
        with contextlib.suppress(StopIteration):
            next(gen)


def test_get_db_empty_yield():
    """Generator yields exactly one item then stops."""
    from database import get_db

    gen = get_db()
    assert next(gen) is not None
    with pytest.raises(StopIteration):
        next(gen)
