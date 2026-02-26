"""
Unit tests for Lambda #5: approval-notifier
(backend/src/lambdas/approval-notifier/handler.py)

Coverage targets:
  - handler()                  — routing to approve / reject / notify
  - handle_approve()           — success, token not found, exception
  - handle_reject()            — success, token not found, exception
  - handle_notify_approver()   — SNS published, SNS skipped when no ARN, DB error re-raised

Run from the backend/ directory:
    pytest tests/ -v --cov=src/lambdas/approval-notifier --cov-report=term-missing
"""
import sys
import os
import json
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# ── Load the handler module via importlib ─────────────────────────────────────
# conftest.py has already injected mock utils into sys.modules.

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/approval-notifier/handler.py")
)
_spec = importlib.util.spec_from_file_location("approval_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["approval_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _api_event(path, method="POST", body=None, path_params=None):
    """Build a minimal API Gateway proxy event."""
    return {
        "httpMethod": method,
        "path": path,
        "pathParameters": path_params or {},
        "body": json.dumps(body) if body else "{}",
    }


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def lambda_context():
    ctx = MagicMock()
    ctx.function_name = "bancafiel-approvalNotifier-dev"
    ctx.aws_request_id = "test-request-id"
    return ctx


@pytest.fixture
def app_summary():
    """Application summary as returned by the DB join query inside handle_notify_approver."""
    return {
        "full_name": "Maria Lopez",
        "loan_amount": 75_000.0,
        "fraud_score": 200,
        "fraud_risk_level": "LOW",
    }


@pytest.fixture
def pending_token():
    return {"task_token": "sfn-task-token-xyz"}


# ── Tests: handler() routing ──────────────────────────────────────────────────

class TestHandlerRouting:
    """handler() must dispatch to the correct function based on the event shape."""

    def test_routes_approve_path_to_handle_approve(self, lambda_context):
        event = _api_event("/api/loans/app-001/approve", path_params={"id": "app-001"})
        with patch.object(mod, "handle_approve", return_value={"statusCode": 200, "body": "{}"}) as mock_fn:
            mod.handler(event, lambda_context)
        mock_fn.assert_called_once_with(event)

    def test_routes_reject_path_to_handle_reject(self, lambda_context):
        event = _api_event("/api/loans/app-001/reject", path_params={"id": "app-001"})
        with patch.object(mod, "handle_reject", return_value={"statusCode": 200, "body": "{}"}) as mock_fn:
            mod.handler(event, lambda_context)
        mock_fn.assert_called_once_with(event)

    def test_routes_step_functions_event_to_handle_notify(self, lambda_context):
        """Events without httpMethod come from Step Functions, not API Gateway."""
        event = {"application_id": "app-001", "task_token": "token-abc", "approver_type": "analyst"}
        with patch.object(mod, "handle_notify_approver", return_value=None) as mock_fn:
            mod.handler(event, lambda_context)
        mock_fn.assert_called_once_with(event)


# ── Tests: handle_approve() ───────────────────────────────────────────────────

class TestHandleApprove:

    def test_success_resumes_step_functions_and_returns_200(self, pending_token):
        event = _api_event(
            "/api/loans/app-001/approve",
            body={"approvedBy": "analyst@bancafiel.com", "notes": "All checks passed"},
            path_params={"id": "app-001"},
        )
        mock_sf = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=pending_token), \
             patch.object(mod, "execute_insert"), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "stepfunctions_client", mock_sf):
            result = mod.handle_approve(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "approved"

        # Step Functions must be resumed with the correct token
        mock_sf.send_task_success.assert_called_once()
        call_kwargs = mock_sf.send_task_success.call_args[1]
        assert call_kwargs["taskToken"] == "sfn-task-token-xyz"
        output = json.loads(call_kwargs["output"])
        assert output["decision"] == "APPROVED"
        assert output["application_id"] == "app-001"

    def test_token_not_found_returns_404(self):
        event = _api_event("/api/loans/missing/approve", path_params={"id": "missing"})
        with patch.object(mod, "execute_query_single", return_value=None):
            result = mod.handle_approve(event)

        assert result["statusCode"] == 404

    def test_db_exception_returns_500(self):
        event = _api_event("/api/loans/app-001/approve", path_params={"id": "app-001"})
        with patch.object(mod, "execute_query_single", side_effect=Exception("DB timeout")):
            result = mod.handle_approve(event)

        assert result["statusCode"] == 500


# ── Tests: handle_reject() ────────────────────────────────────────────────────

class TestHandleReject:

    def test_success_resumes_step_functions_with_rejected_decision(self, pending_token):
        event = _api_event(
            "/api/loans/app-001/reject",
            body={"rejectedBy": "senior@bancafiel.com", "reason": "Suspiciously high DTI"},
            path_params={"id": "app-001"},
        )
        mock_sf = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=pending_token), \
             patch.object(mod, "execute_insert"), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "stepfunctions_client", mock_sf):
            result = mod.handle_reject(event)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["status"] == "rejected"

        call_kwargs = mock_sf.send_task_success.call_args[1]
        output = json.loads(call_kwargs["output"])
        assert output["decision"] == "REJECTED"
        assert output["reason"] == "Suspiciously high DTI"

    def test_token_not_found_returns_404(self):
        event = _api_event("/api/loans/missing/reject", path_params={"id": "missing"})
        with patch.object(mod, "execute_query_single", return_value=None):
            result = mod.handle_reject(event)

        assert result["statusCode"] == 404

    def test_db_exception_returns_500(self):
        event = _api_event("/api/loans/app-001/reject", path_params={"id": "app-001"})
        with patch.object(mod, "execute_query_single", side_effect=Exception("Network error")):
            result = mod.handle_reject(event)

        assert result["statusCode"] == 500


# ── Tests: handle_notify_approver() ──────────────────────────────────────────

class TestHandleNotifyApprover:

    def test_stores_task_token_and_publishes_to_sns(self, app_summary):
        event = {
            "application_id": "app-001",
            "task_token": "sfn-token-abc",
            "approver_type": "analyst",
        }
        mock_sns = MagicMock()

        with patch.object(mod, "execute_insert"), \
             patch.object(mod, "execute_query_single", return_value=app_summary), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "sns_client", mock_sns), \
             patch.dict(os.environ, {"APPROVER_SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123:approvers"}):
            mod.handle_notify_approver(event)

        mock_sns.publish.assert_called_once()
        call_kwargs = mock_sns.publish.call_args[1]
        assert call_kwargs["TopicArn"] == "arn:aws:sns:us-east-1:123:approvers"
        # Customer name must appear in the notification body
        assert "Maria Lopez" in call_kwargs["Message"]
        assert "75,000.00" in call_kwargs["Message"]

    def test_skips_sns_publish_when_no_topic_arn(self, app_summary):
        """Without APPROVER_SNS_TOPIC_ARN, SNS must NOT be called."""
        event = {"application_id": "app-001", "task_token": "sfn-token-abc"}
        mock_sns = MagicMock()
        os.environ.pop("APPROVER_SNS_TOPIC_ARN", None)

        with patch.object(mod, "execute_insert"), \
             patch.object(mod, "execute_query_single", return_value=app_summary), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "sns_client", mock_sns):
            mod.handle_notify_approver(event)

        mock_sns.publish.assert_not_called()

    def test_db_error_propagates_to_step_functions(self):
        """
        Errors must NOT be swallowed — they propagate so Step Functions
        can mark the task as failed and retry.
        """
        event = {"application_id": "app-001", "task_token": "sfn-token-abc"}
        with patch.object(mod, "execute_insert", side_effect=Exception("DB is down")):
            with pytest.raises(Exception, match="DB is down"):
                mod.handle_notify_approver(event)
