"""
Unit tests for Lambda #7: notification-sender
(backend/src/lambdas/notification-sender/handler.py)
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
    execute_query_single=MagicMock(),
    create_application_history=MagicMock(),
)
sys.modules["utils.logger"] = types.SimpleNamespace(
    setup_logger=lambda name: MagicMock(),
    log_event=lambda logger, event_type, data: None,
    log_error=lambda logger, error_type, error, context=None: None,
)


_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/notification-sender/handler.py")
)
_spec = importlib.util.spec_from_file_location("notification_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["notification_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


def _app_record(application_type="LOAN"):
    return {
        "loan_amount": 50000.0,
        "application_type": application_type,
        "full_name": "Maria Lopez",
        "email": "maria@example.com",
    }


class TestNotificationSenderHandler(unittest.TestCase):
    def test_returns_200_and_sends_email_on_success(self):
        event = {"application_id": "app-001", "type": "approved"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Notification sent: approved", result["message"])
        mock_ses.send_email.assert_called_once()
        kwargs = mock_ses.send_email.call_args[1]
        self.assertEqual(kwargs["Destination"]["ToAddresses"], ["maria@example.com"])
        self.assertIn("APROBADA", kwargs["Message"]["Subject"]["Data"])
        self.assertEqual(kwargs["Source"], mod.FROM_EMAIL)

    def test_returns_404_when_application_not_found(self):
        event = {"application_id": "missing-id", "type": "received"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=None), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 404)
        mock_ses.send_email.assert_not_called()

    def test_falls_back_to_received_template_for_unknown_type(self):
        event = {"application_id": "app-001", "type": "unexpected_type"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        kwargs = mock_ses.send_email.call_args[1]
        self.assertIn("Hemos recibido su solicitud", kwargs["Message"]["Subject"]["Data"])

    def test_uses_default_received_type_when_type_missing(self):
        event = {"application_id": "app-001"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history") as mock_history, \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["message"], "Notification sent: received")
        args, kwargs = mock_history.call_args
        self.assertEqual(args[1], "email_sent_received")
        self.assertIn("received", kwargs["notes"])

    def test_credit_application_uses_credit_card_copy_in_email_body(self):
        event = {"application_id": "app-001", "type": "rejected"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record(application_type="CARD")), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        kwargs = mock_ses.send_email.call_args[1]
        body_text = kwargs["Message"]["Body"]["Text"]["Data"]
        self.assertIn("tarjeta de crédito", body_text)

    def test_ses_message_rejected_does_not_fail_workflow(self):
        class _SESMessageRejected(Exception):
            pass

        class _FakeSESClient:
            class exceptions:
                MessageRejected = _SESMessageRejected

            def __init__(self):
                self.send_email_calls = 0

            def send_email(self, **kwargs):
                self.send_email_calls += 1
                raise _SESMessageRejected("Email address is not verified")

        fake_ses = _FakeSESClient()
        event = {"application_id": "app-001", "type": "received"}

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history") as mock_history, \
             patch.object(mod, "ses_client", fake_ses):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(fake_ses.send_email_calls, 1)
        mock_history.assert_called_once()

    def test_returns_500_on_unexpected_exception(self):
        event = {"application_id": "app-001", "type": "received"}

        with patch.object(mod, "execute_query_single", side_effect=Exception("DB connection failed")):
            result = mod.handler(event, context=MagicMock())

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("DB connection failed", result["error"])
