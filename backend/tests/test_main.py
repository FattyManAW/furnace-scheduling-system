"""Tests for main.py — root, health, CORS, exception handlers"""

import os
from unittest.mock import MagicMock, patch

import pytest
from starlette.exceptions import HTTPException as StarletteHTTPException


class TestRootEndpoint:
    """Coverage: L62 (root return body)"""

    def test_root_endpoint(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "干式套管最佳化排爐系統"
        assert data["version"] == "2.0.0"
        assert data["docs"] == "/docs"
        assert data["api"] == "/openapi.json"


class TestHealthEndpoint:
    """Coverage: L74-80 (health body)"""

    def test_health_endpoint(self, client):
        """L74, 78-79, 80: health with no GIT_COMMIT file → 'unknown'"""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["commit"] == "unknown"
        assert data["version"] == "2.0.0"

    def test_healthz_endpoint(self, client):
        """L71: /healthz alias → same as /health"""
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_health_direct_with_commit(self, monkeypatch):
        """Direct test: call health() with monkeypatched open"""
        import main as _main

        class FakeFile:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self):
                return "abc1234"
            def strip(self):
                return "abc1234"

        def fake_open(path):
            if path == "/app/GIT_COMMIT":
                return FakeFile()
            raise FileNotFoundError(f"No such file: {path}")

        monkeypatch.setattr("builtins.open", fake_open)
        result = _main.health()
        assert result["commit"] == "abc1234"


class TestCORS:
    """Coverage: L34 (CORS with ALLOWED_ORIGINS env var set)"""

    def test_cors_with_env_var(self, monkeypatch):
        """L32-34: ALLOWED_ORIGINS set → custom origins list"""
        monkeypatch.setenv("ALLOWED_ORIGINS", "https://example.com,https://foo.bar")
        import importlib

        import main as _main
        importlib.reload(_main)
        assert "https://example.com" in str(_main._origins)
        assert "https://foo.bar" in str(_main._origins)

    def test_cors_env_var_empty_string(self, monkeypatch):
        """L32-35: ALLOWED_ORIGINS set to empty → fallback to defaults"""
        monkeypatch.setenv("ALLOWED_ORIGINS", "")
        import importlib

        import main as _main
        importlib.reload(_main)
        assert "http://localhost:5173" in _main._origins


class TestExceptionHandlers:
    """Coverage: L108 (db handler), L115 (generic handler)"""

    def test_http_exception_handler(self, client):
        """L92-97: HTTPException → JSON response with type"""
        import asyncio

        from fastapi.requests import Request

        import main as _main

        req = MagicMock(spec=Request)
        exc = StarletteHTTPException(status_code=403, detail="forbidden")
        loop = asyncio.new_event_loop()
        resp = loop.run_until_complete(_main.http_exc_handler(req, exc))
        loop.close()
        assert resp.status_code == 403
        data = resp.body.decode()
        assert "forbidden" in data
        assert "http_exception" in data

    def test_validation_exception_handler(self, client):
        """L99-104: validation error → 422"""
        resp = client.post("/api/v1/orders/", json={
            "plan_no": "X",
            "voltage_kv": "not-a-number",
        })
        assert resp.status_code == 422
        data = resp.json()
        assert data["type"] == "validation_error"

    def test_db_exception_handler_direct(self):
        """L106-111: SQLAlchemyError → 500"""
        import asyncio

        from fastapi.requests import Request
        from sqlalchemy.exc import SQLAlchemyError

        import main as _main

        req = MagicMock(spec=Request)
        exc = SQLAlchemyError("db error")
        loop = asyncio.new_event_loop()
        resp = loop.run_until_complete(_main.db_exc_handler(req, exc))
        loop.close()
        assert resp.status_code == 500
        data = resp.body.decode()
        assert "資料庫錯誤" in data
        assert "database_error" in data

    def test_generic_exception_handler_direct(self):
        """L113-118: generic Exception → 500"""
        import asyncio

        from fastapi.requests import Request

        import main as _main

        req = MagicMock(spec=Request)
        exc = ValueError("kaboom")
        loop = asyncio.new_event_loop()
        resp = loop.run_until_complete(_main.generic_exc_handler(req, exc))
        loop.close()
        assert resp.status_code == 500
        data = resp.body.decode()
        assert "kaboom" in data
        assert "internal_error" in data


class TestMainBlock:
    """Coverage: L122-128 (if __name__ == '__main__') — guard entry point"""

    def test_main_guard_block(self, monkeypatch):
        """L122-128: execute module as __main__ with mocked uvicorn.run"""
        monkeypatch.setenv("PORT", "9999")
        import importlib
        import sys

        # Remove main from sys.modules so it re-executes with __name__='__main__'
        # under runpy
        sys.modules.pop("main", None)

        try:
            with patch("uvicorn.run") as mock_run:
                import runpy
                runpy.run_module("main", run_name="__main__")
                mock_run.assert_called_once()
        finally:
            # Re-import main normally so other tests don't break
            sys.modules.pop("main", None)
            importlib.import_module("main")
