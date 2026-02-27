"""
Unit tests for Lambda #6: erp-updater
(backend/src/lambdas/erp-updater/handler.py)
"""
import sys
import os
import importlib.util
import unittest
import types
from unittest.mock import patch, MagicMock

try:
    import boto3  # noqa: F401
except ModuleNotFoundError:
    sys.modules["boto3"] = types.SimpleNamespace(client=lambda *args, **kwargs: MagicMock())

# unittest does not auto-load tests/conftest.py, so inject lightweight utils fakes here.
sys.modules.setdefault("utils", types.ModuleType("utils"))
sys.modules["utils.database"] = types.SimpleNamespace(
    execute_insert=MagicMock(),
    execute_query_single=MagicMock(),
    create_application_history=MagicMock(),
)
sys.modules["utils.logger"] = types.SimpleNamespace(
    setup_logger=lambda name: MagicMock(),
    log_event=lambda logger, event_type, data: None,
    log_error=lambda logger, error_type, error, context=None: None,
)

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/erp-updater/handler.py")
)
_spec = importlib.util.spec_from_file_location("erp_updater_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["erp_updater_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


class TestERPUpdaterHandler(unittest.TestCase):
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

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["application_id"], "app-001")
        self.assertEqual(result["status"], "APPROVED")

        mock_insert.assert_called_once()
        query = mock_insert.call_args[0][0]
        params = mock_insert.call_args[0][1]
        self.assertIn("SET status = 'APPROVED'", query)
        self.assertEqual(params[0], "analyst@bancafiel.com")
        self.assertEqual(params[1], "All checks passed")
        self.assertEqual(params[4], "app-001")

        mock_history.assert_called_once()
        self.assertEqual(mock_history.call_args[0][0], "app-001")
        self.assertEqual(mock_history.call_args[0][1], "approved")
        self.assertEqual(mock_history.call_args[0][2], "analyst@bancafiel.com")
        self.assertEqual(mock_history.call_args[1]["metadata"]["status"], "APPROVED")

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

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["application_id"], "app-002")
        self.assertEqual(result["status"], "REJECTED")

        mock_insert.assert_called_once()
        query = mock_insert.call_args[0][0]
        params = mock_insert.call_args[0][1]
        self.assertIn("SET status = 'REJECTED'", query)
        self.assertEqual(params[0], "risk@bancafiel.com")
        self.assertEqual(params[1], "Suspicious data mismatch")
        self.assertEqual(params[4], "app-002")

        mock_history.assert_called_once()
        self.assertEqual(mock_history.call_args[0][0], "app-002")
        self.assertEqual(mock_history.call_args[0][1], "rejected")
        self.assertEqual(mock_history.call_args[0][2], "risk@bancafiel.com")
        self.assertEqual(mock_history.call_args[1]["metadata"]["status"], "REJECTED")
        self.assertEqual(mock_history.call_args[1]["metadata"]["reason"], "Suspicious data mismatch")

    def test_rejected_status_uses_system_when_rejected_by_missing(self):
        event = {
            "application_id": "app-003",
            "status": "REJECTED",
            "reason": "Incomplete docs",
        }

        with patch.object(mod, "execute_insert") as mock_insert, \
             patch.object(mod, "create_application_history") as mock_history:
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        params = mock_insert.call_args[0][1]
        self.assertEqual(params[0], "system")
        self.assertEqual(mock_history.call_args[0][2], "system")

    def test_unknown_status_returns_200_without_db_updates(self):
        event = {"application_id": "app-004", "status": "PENDING"}

        with patch.object(mod, "execute_insert") as mock_insert, \
             patch.object(mod, "create_application_history") as mock_history:
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["status"], "PENDING")
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

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("DB timeout", result["error"])
