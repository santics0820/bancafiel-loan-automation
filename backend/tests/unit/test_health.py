"""
Unit tests for API route: health
(backend/src/api/routes/health.py)
"""
import sys
import os
import json
import importlib.util
import unittest
import types
from unittest.mock import patch, MagicMock


# unittest does not auto-load tests/conftest.py, so inject lightweight utils fakes here.
sys.modules.setdefault("utils", types.ModuleType("utils"))
sys.modules["utils.database"] = types.SimpleNamespace(
    execute_query_single=MagicMock(),
)
sys.modules["utils.response"] = types.SimpleNamespace(
    success_response=lambda d, s=200: {"statusCode": s, "body": json.dumps(d, default=str)},
    error_response=lambda m, s=400, c=None: {"statusCode": s, "body": json.dumps({"error": m})},
)

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/api/routes/health.py")
)
_spec = importlib.util.spec_from_file_location("health_route", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["health_route"] = mod
_spec.loader.exec_module(mod)


class TestHealthRoute(unittest.TestCase):
    def test_health_healthy_when_db_ping_ok(self):
        with patch.object(mod, "execute_query_single", return_value={"ok": 1, "server_time": "2026-02-26T00:00:00Z"}):
            result = mod.handler(event={}, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["services"]["api"], "ok")
        self.assertEqual(body["services"]["database"], "ok")
        self.assertEqual(body["version"], "1.0.0")
        self.assertIn("timestamp", body)

    def test_health_degraded_when_db_ping_not_ok(self):
        with patch.object(mod, "execute_query_single", return_value={"ok": 0}):
            result = mod.handler(event={}, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["services"]["database"], "error")

    def test_health_degraded_when_db_ping_empty(self):
        with patch.object(mod, "execute_query_single", return_value=None):
            result = mod.handler(event={}, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["status"], "degraded")
        self.assertEqual(body["services"]["database"], "error")

    def test_health_returns_503_on_exception(self):
        with patch.object(mod, "execute_query_single", side_effect=Exception("DB unavailable")):
            result = mod.handler(event={}, context=MagicMock())

        self.assertEqual(result["statusCode"], 503)
        body = json.loads(result["body"])
        self.assertIn("Health check failed", body["error"])
        self.assertIn("DB unavailable", body["error"])
