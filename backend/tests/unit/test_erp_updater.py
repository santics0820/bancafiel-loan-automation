"""
Unit tests for Lambda #6: erp-updater
(backend/src/lambdas/erp-updater/handler.py)

Run from the backend/ directory:
    python -m pytest tests/ -v --cov=src/lambdas/erp-updater --cov-report=term-missing
"""
import sys
import os
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# conftest.py injects utils.database, utils.logger into sys.modules before this loads.

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/erp-updater/handler.py")
)
_spec = importlib.util.spec_from_file_location("erp_updater_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["erp_updater_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


class TestERPUpdaterHandler:
    def test_approved_status_updates_application_and_history(self):
        event = {
            "application_id": "app-001",
            "status": "APPROVED",
            "approved_by": "analyst@bancafiel.com",
            "notes": "All checks passed",
        }

        with patch.object(mod, "execute_insert") as mock_insert, \
             patch.object(mod, "create_application_history") as mock_history:
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        assert result["application_id"] == "app-001"
        assert result["status"] == "APPROVED"

        mock_insert.assert_called_once()
        query = mock_insert.call_args[0][0]
        params = mock_insert.call_args[0][1]
        assert "SET status = 'APPROVED'" in query
        assert params[0] == "analyst@bancafiel.com"
        assert params[1] == "All checks passed"
        assert params[4] == "app-001"

        mock_history.assert_called_once()
        assert mock_history.call_args[0][0] == "app-001"
        assert mock_history.call_args[0][1] == "approved"
        assert mock_history.call_args[0][2] == "analyst@bancafiel.com"
        assert mock_history.call_args[1]["metadata"]["status"] == "APPROVED"

    def test_rejected_status_updates_application_and_history(self):
        event = {
            "application_id": "app-002",
            "status": "REJECTED",
            "rejected_by": "risk@bancafiel.com",
            "reason": "Suspicious data mismatch",
        }

        with patch.object(mod, "execute_insert") as mock_insert, \
             patch.object(mod, "create_application_history") as mock_history:
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        assert result["application_id"] == "app-002"
        assert result["status"] == "REJECTED"

        mock_insert.assert_called_once()
        query = mock_insert.call_args[0][0]
        params = mock_insert.call_args[0][1]
        assert "SET status = 'REJECTED'" in query
        assert params[0] == "risk@bancafiel.com"
        assert params[1] == "Suspicious data mismatch"
        assert params[4] == "app-002"

        mock_history.assert_called_once()
        assert mock_history.call_args[0][0] == "app-002"
        assert mock_history.call_args[0][1] == "rejected"
        assert mock_history.call_args[0][2] == "risk@bancafiel.com"
        assert mock_history.call_args[1]["metadata"]["status"] == "REJECTED"
        assert mock_history.call_args[1]["metadata"]["reason"] == "Suspicious data mismatch"

    def test_rejected_status_uses_system_when_rejected_by_missing(self):
        event = {
            "application_id": "app-003",
            "status": "REJECTED",
            "reason": "Incomplete docs",
        }

        with patch.object(mod, "execute_insert") as mock_insert, \
             patch.object(mod, "create_application_history") as mock_history:
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        params = mock_insert.call_args[0][1]
        assert params[0] == "system"
        assert mock_history.call_args[0][2] == "system"

    def test_unknown_status_returns_200_without_db_updates(self):
        event = {"application_id": "app-004", "status": "PENDING"}

        with patch.object(mod, "execute_insert") as mock_insert, \
             patch.object(mod, "create_application_history") as mock_history:
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        assert result["status"] == "PENDING"
        mock_insert.assert_not_called()
        mock_history.assert_not_called()

    def test_returns_500_on_unexpected_exception(self):
        event = {
            "application_id": "app-005",
            "status": "APPROVED",
            "approved_by": "analyst@bancafiel.com",
        }

        with patch.object(mod, "execute_insert", side_effect=Exception("DB timeout")):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 500
        assert "DB timeout" in result["error"]
