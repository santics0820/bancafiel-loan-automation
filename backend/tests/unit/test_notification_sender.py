"""
Unit tests for Lambda #7: notification-sender
(backend/src/lambdas/notification-sender/handler.py)

Run from the backend/ directory:
    python -m pytest tests/ -v --cov=src/lambdas/notification-sender --cov-report=term-missing
"""
import sys
import os
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# conftest.py injects utils.database, utils.logger into sys.modules before this loads.

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


class TestNotificationSenderHandler:
    def test_returns_200_and_sends_email_on_success(self):
        event = {"application_id": "app-001", "type": "approved"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        assert "Notification sent: approved" in result["message"]
        mock_ses.send_email.assert_called_once()
        kwargs = mock_ses.send_email.call_args[1]
        assert kwargs["Destination"]["ToAddresses"] == ["maria@example.com"]
        assert "APROBADA" in kwargs["Message"]["Subject"]["Data"]
        assert kwargs["Source"] == mod.FROM_EMAIL

    def test_returns_404_when_application_not_found(self):
        event = {"application_id": "missing-id", "type": "received"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=None), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 404
        mock_ses.send_email.assert_not_called()

    def test_falls_back_to_received_template_for_unknown_type(self):
        event = {"application_id": "app-001", "type": "unexpected_type"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        kwargs = mock_ses.send_email.call_args[1]
        assert "Hemos recibido su solicitud" in kwargs["Message"]["Subject"]["Data"]

    def test_uses_default_received_type_when_type_missing(self):
        event = {"application_id": "app-001"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record()), \
             patch.object(mod, "create_application_history") as mock_history, \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        assert result["message"] == "Notification sent: received"
        args, kwargs = mock_history.call_args
        assert args[1] == "email_sent_received"
        assert "received" in kwargs["notes"]

    def test_credit_application_uses_credit_card_copy_in_email_body(self):
        event = {"application_id": "app-001", "type": "rejected"}
        mock_ses = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=_app_record(application_type="CARD")), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "ses_client", mock_ses):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 200
        kwargs = mock_ses.send_email.call_args[1]
        body_text = kwargs["Message"]["Body"]["Text"]["Data"]
        assert "tarjeta de crédito" in body_text

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

        assert result["statusCode"] == 200
        assert fake_ses.send_email_calls == 1
        mock_history.assert_called_once()

    def test_returns_500_on_unexpected_exception(self):
        event = {"application_id": "app-001", "type": "received"}

        with patch.object(mod, "execute_query_single", side_effect=Exception("DB connection failed")):
            result = mod.handler(event, context=MagicMock())

        assert result["statusCode"] == 500
        assert "DB connection failed" in result["error"]
