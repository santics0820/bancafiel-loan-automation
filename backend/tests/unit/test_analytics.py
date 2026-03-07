"""
Unit tests for API route: analytics
(backend/src/api/routes/analytics.py)

Run from the backend/ directory:
    python -m pytest tests/ -v --cov=src/api/routes/analytics --cov-report=term-missing
"""
import sys
import os
import json
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# conftest.py injects utils.database, utils.logger, utils.response into sys.modules before this loads.

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/api/routes/analytics.py")
)
_spec = importlib.util.spec_from_file_location("analytics_route", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["analytics_route"] = mod
_spec.loader.exec_module(mod)


class TestAnalyticsRoute:
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

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["totalApplications"] == 3
        assert body["approved"] == 2
        assert body["rejected"] == 1
        assert body["pending"] == 0
        assert body["fraudAlerts"] == 1
        assert body["approvalRate"] == 0.67
        assert body["averageProcessingTime"] == 45.4
        assert len(body["volumeByDay"]) == 2
        assert body["volumeByDay"][0]["applications"] == 1

        stats_args = mock_stats.call_args[0]
        assert stats_args[1] == ("2026-02-01", "2026-02-15")

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

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["totalApplications"] == 0
        assert body["approvalRate"] == 0
        assert body["averageProcessingTime"] == 0.0
        assert body["volumeByDay"] == []
        mock_daily.assert_called_once()

    def test_get_analytics_returns_500_on_exception(self):
        event = {"queryStringParameters": {"startDate": "2026-02-01", "endDate": "2026-02-15"}}

        with patch.object(mod, "execute_query_single", side_effect=Exception("DB timeout")):
            result = mod.get_analytics(event, context=MagicMock())

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert body["message"] == "Failed to retrieve analytics"
