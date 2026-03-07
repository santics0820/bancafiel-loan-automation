"""
Unit tests for API route: health
(backend/src/api/routes/health.py)

Run from the backend/ directory:
    python -m pytest tests/ -v --cov=src/api/routes/health --cov-report=term-missing
"""
import sys
import os
import json
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# conftest.py injects utils.database, utils.response into sys.modules before this loads.

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/api/routes/health.py")
)
_spec = importlib.util.spec_from_file_location("health_route", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["health_route"] = mod
_spec.loader.exec_module(mod)


class TestHealthRoute:
    def test_health_healthy_when_db_ping_ok(self):
        with patch.object(mod, "execute_query_single", return_value={"ok": 1, "server_time": "2026-02-26T00:00:00Z"}):
            result = mod.handler(event={}, context=MagicMock())

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "healthy"
        assert body["services"]["api"] == "ok"
        assert body["services"]["database"] == "ok"
        assert body["version"] == "1.0.0"
        assert "timestamp" in body

    def test_health_degraded_when_db_ping_not_ok(self):
        with patch.object(mod, "execute_query_single", return_value={"ok": 0}):
            result = mod.handler(event={}, context=MagicMock())

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "degraded"
        assert body["services"]["database"] == "error"

    def test_health_degraded_when_db_ping_empty(self):
        with patch.object(mod, "execute_query_single", return_value=None):
            result = mod.handler(event={}, context=MagicMock())

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "degraded"
        assert body["services"]["database"] == "error"

    def test_health_returns_503_on_exception(self):
        with patch.object(mod, "execute_query_single", side_effect=Exception("DB unavailable")):
            result = mod.handler(event={}, context=MagicMock())

        assert result["statusCode"] == 503
        body = json.loads(result["body"])
        assert "Health check failed" in body["message"]
        assert "DB unavailable" in body["message"]
