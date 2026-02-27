"""
Unit tests for API route: analytics
(backend/src/api/routes/analytics.py)
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
    execute_query=MagicMock(),
    execute_query_single=MagicMock(),
)
sys.modules["utils.logger"] = types.SimpleNamespace(
    setup_logger=lambda name: MagicMock(),
    log_error=lambda logger, error_type, error, context=None: None,
)
sys.modules["utils.response"] = types.SimpleNamespace(
    success_response=lambda d, s=200: {"statusCode": s, "body": json.dumps(d, default=str)},
    error_response=lambda m, s=400, c=None: {"statusCode": s, "body": json.dumps({"error": m})},
)

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/api/routes/analytics.py")
)
_spec = importlib.util.spec_from_file_location("analytics_route", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["analytics_route"] = mod
_spec.loader.exec_module(mod)


class TestAnalyticsRoute(unittest.TestCase):
    def test_get_analytics_success_with_explicit_dates(self):
        event = {
            "queryStringParameters": {
                "startDate": "2026-02-01",
                "endDate": "2026-02-15",
            }
        }
        stats = {
            "total_applications": 3,
            "approved": 2,
            "rejected": 1,
            "pending": 0,
            "fraud_alerts": 1,
            "avg_processing_minutes": 45.4,
        }
        daily = [
            {"date": "2026-02-01", "applications": 1},
            {"date": "2026-02-02", "applications": 2},
        ]

        with patch.object(mod, "execute_query_single", return_value=stats) as mock_stats, \
             patch.object(mod, "execute_query", return_value=daily):
            result = mod.get_analytics(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["totalApplications"], 3)
        self.assertEqual(body["approved"], 2)
        self.assertEqual(body["rejected"], 1)
        self.assertEqual(body["pending"], 0)
        self.assertEqual(body["fraudAlerts"], 1)
        self.assertEqual(body["approvalRate"], 0.67)
        self.assertEqual(body["averageProcessingTime"], 45.4)
        self.assertEqual(len(body["volumeByDay"]), 2)
        self.assertEqual(body["volumeByDay"][0]["applications"], 1)

        stats_args = mock_stats.call_args[0]
        self.assertEqual(stats_args[1], ("2026-02-01", "2026-02-15"))

    def test_get_analytics_uses_default_dates_and_zero_approval_rate(self):
        event = {"queryStringParameters": None}
        stats = {
            "total_applications": 0,
            "approved": 0,
            "rejected": 0,
            "pending": 0,
            "fraud_alerts": 0,
            "avg_processing_minutes": None,
        }

        with patch.object(mod, "execute_query_single", return_value=stats), \
             patch.object(mod, "execute_query", return_value=[]) as mock_daily:
            result = mod.get_analytics(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["totalApplications"], 0)
        self.assertEqual(body["approvalRate"], 0)
        self.assertEqual(body["averageProcessingTime"], 0.0)
        self.assertEqual(body["volumeByDay"], [])
        mock_daily.assert_called_once()

    def test_get_analytics_returns_500_on_exception(self):
        event = {"queryStringParameters": {"startDate": "2026-02-01", "endDate": "2026-02-15"}}

        with patch.object(mod, "execute_query_single", side_effect=Exception("DB timeout")):
            result = mod.get_analytics(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["error"], "Failed to retrieve analytics")
