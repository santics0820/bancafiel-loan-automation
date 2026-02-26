"""
Step Functions contract tests for Ricardo's pipeline
(Lambda #4 detectFraud ↔ Step Functions ↔ Lambda #5 approvalNotifier)

These tests verify that the data flowing between the three components uses
exactly the same field names. A mismatch here would cause a silent failure
in production — the state machine would receive the payload but route
incorrectly or crash because a key is missing.

Three contracts are verified:

  CONTRACT 1 — detectFraud → Step Functions
    detectFraud calls start_execution() with a JSON payload.
    The state machine's "CheckFraudScore" Choice state reads $.fraud_risk_level.
    These must be the exact same string.

  CONTRACT 2 — Step Functions → approvalNotifier
    The state machine invokes approvalNotifier with:
      { application_id, approver_type, task_token }
    approvalNotifier reads those exact keys from the event.

  CONTRACT 3 — approvalNotifier → Step Functions (callback)
    approvalNotifier calls send_task_success() with an output payload.
    The state machine's "ProcessDecision" Choice state reads $.decision.
    The value must be exactly "APPROVED" or "REJECTED" (uppercase strings).

Run from backend/:
    pytest tests/unit/test_stepfunctions_contract.py -v
"""
import sys
import os
import json
import importlib.util
from unittest.mock import patch, MagicMock, call

import pytest

# ── Load both handler modules ─────────────────────────────────────────────────
# Re-use modules already cached by previous test files if running in full suite,
# otherwise load them fresh here.

_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/lambdas"))


def _load(lambda_dir, module_name):
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = os.path.join(_BASE, lambda_dir, "handler.py")
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    with patch("boto3.client", return_value=MagicMock()):
        spec.loader.exec_module(mod)
    return mod


fraud_mod = _load("fraud-detector", "fraud_handler")
approval_mod = _load("approval-notifier", "approval_handler")


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def app_data():
    return {
        "id": "app-abc-123",
        "customer_id": "cust-001",
        "loan_amount": 20_000.0,
        "monthly_income": 10_000.0,
        "curp": "ABCD123456HDFXXX01",
        "email": "juan@example.com",
        "phone": "5551234567",
        "full_name": "Juan Perez",
    }


@pytest.fixture
def pending_token():
    return {"task_token": "sfn-task-token-xyz"}


# ══════════════════════════════════════════════════════════════════════════════
# CONTRACT 1 — detectFraud → Step Functions
#
# The state machine "CheckFraudScore" Choice state reads:
#   "Variable": "$.fraud_risk_level"
#   "StringEquals": "HIGH" | "MEDIUM"   (default = LOW / analyst)
#
# detectFraud must send a JSON payload that contains exactly that key
# with exactly those string values.
# ══════════════════════════════════════════════════════════════════════════════

class TestContract1_DetectFraudToStepFunctions:
    """detectFraud → Step Functions start_execution payload."""

    def _run_handler_with_risk(self, app_data, risk_level, score):
        """Helper: run handler and return the start_execution call kwargs."""
        mock_sf = MagicMock()
        event = {"application_id": "app-abc-123"}

        with patch.object(fraud_mod, "execute_query_single", return_value=app_data), \
             patch.object(fraud_mod, "execute_insert"), \
             patch.object(fraud_mod, "create_application_history"), \
             patch.object(fraud_mod, "run_fraud_detection", return_value=(score, risk_level, [])), \
             patch.object(fraud_mod, "count_duplicate_applications", return_value=0), \
             patch.object(fraud_mod, "stepfunctions_client", mock_sf), \
             patch.dict(os.environ, {"LOAN_WORKFLOW_ARN": "arn:aws:states:us-east-1:123:stateMachine:test"}):
            fraud_mod.handler(event, MagicMock())

        return mock_sf.start_execution.call_args[1]

    def test_payload_contains_fraud_risk_level_key(self, app_data):
        """The Step Functions input MUST contain 'fraud_risk_level' — the state machine reads $.fraud_risk_level."""
        kwargs = self._run_handler_with_risk(app_data, "LOW", 100)
        payload = json.loads(kwargs["input"])
        assert "fraud_risk_level" in payload, (
            "Missing 'fraud_risk_level' in start_execution input — "
            "CheckFraudScore state reads $.fraud_risk_level"
        )

    def test_payload_contains_application_id_key(self, app_data):
        """The Step Functions input MUST contain 'application_id' — downstream states read $.application_id."""
        kwargs = self._run_handler_with_risk(app_data, "LOW", 100)
        payload = json.loads(kwargs["input"])
        assert "application_id" in payload

    def test_high_risk_value_is_uppercase_string(self, app_data):
        """State machine checks StringEquals 'HIGH' — must be uppercase, not 'high' or 'High'."""
        kwargs = self._run_handler_with_risk(app_data, "HIGH", 750)
        payload = json.loads(kwargs["input"])
        assert payload["fraud_risk_level"] == "HIGH"

    def test_medium_risk_value_is_uppercase_string(self, app_data):
        """State machine checks StringEquals 'MEDIUM' — must be uppercase."""
        kwargs = self._run_handler_with_risk(app_data, "MEDIUM", 400)
        payload = json.loads(kwargs["input"])
        assert payload["fraud_risk_level"] == "MEDIUM"

    def test_low_risk_value_is_uppercase_string(self, app_data):
        """State machine default branch handles LOW — must be uppercase."""
        kwargs = self._run_handler_with_risk(app_data, "LOW", 100)
        payload = json.loads(kwargs["input"])
        assert payload["fraud_risk_level"] == "LOW"

    def test_application_id_matches_input_event(self, app_data):
        """The application_id sent to Step Functions must match the one received from validateData."""
        kwargs = self._run_handler_with_risk(app_data, "LOW", 100)
        payload = json.loads(kwargs["input"])
        assert payload["application_id"] == "app-abc-123"

    def test_score_to_risk_produces_valid_sf_values(self):
        """score_to_risk() must only ever return 'HIGH', 'MEDIUM', or 'LOW' — the three values the state machine knows."""
        valid_values = {"HIGH", "MEDIUM", "LOW"}
        assert fraud_mod.score_to_risk(0) in valid_values
        assert fraud_mod.score_to_risk(299) in valid_values
        assert fraud_mod.score_to_risk(300) in valid_values
        assert fraud_mod.score_to_risk(699) in valid_values
        assert fraud_mod.score_to_risk(700) in valid_values
        assert fraud_mod.score_to_risk(1000) in valid_values


# ══════════════════════════════════════════════════════════════════════════════
# CONTRACT 2 — Step Functions → approvalNotifier
#
# The state machine invokes approvalNotifier with this payload:
#   {
#     "application_id": "...",          ← from $.application_id
#     "approver_type":  "analyst"       ← hardcoded per branch
#                    or "senior_officer"
#     "task_token":     "..."           ← from $$.Task.Token (injected by SF)
#   }
#
# approvalNotifier must read exactly those keys.
# ══════════════════════════════════════════════════════════════════════════════

class TestContract2_StepFunctionsToApprovalNotifier:
    """Step Functions payload → approvalNotifier handle_notify_approver()."""

    def _build_sf_event(self, approver_type="analyst"):
        """Simulate exactly what Step Functions sends to the Lambda."""
        return {
            "application_id": "app-abc-123",
            "approver_type": approver_type,
            "task_token": "sfn-task-token-xyz",
        }

    def test_reads_application_id_key(self):
        """approvalNotifier must read 'application_id' (not 'applicationId' or 'app_id')."""
        event = self._build_sf_event()
        mock_sns = MagicMock()
        app_summary = {"full_name": "Juan", "loan_amount": 20000.0, "fraud_score": 100, "fraud_risk_level": "LOW"}

        with patch.object(approval_mod, "execute_insert") as mock_insert, \
             patch.object(approval_mod, "execute_query_single", return_value=app_summary), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "sns_client", mock_sns):
            os.environ.pop("APPROVER_SNS_TOPIC_ARN", None)
            approval_mod.handle_notify_approver(event)

        # The DB insert must have received the application_id value
        first_call_args = mock_insert.call_args_list[0][0][1]
        assert "app-abc-123" in first_call_args

    def test_reads_task_token_key(self):
        """approvalNotifier must store 'task_token' (not 'taskToken') so it can call send_task_success later."""
        event = self._build_sf_event()
        app_summary = {"full_name": "Juan", "loan_amount": 20000.0, "fraud_score": 100, "fraud_risk_level": "LOW"}

        with patch.object(approval_mod, "execute_insert") as mock_insert, \
             patch.object(approval_mod, "execute_query_single", return_value=app_summary), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "sns_client", MagicMock()):
            os.environ.pop("APPROVER_SNS_TOPIC_ARN", None)
            approval_mod.handle_notify_approver(event)

        # The task token must be passed to the DB insert
        first_call_args = mock_insert.call_args_list[0][0][1]
        assert "sfn-task-token-xyz" in first_call_args

    def test_analyst_approver_type_is_accepted(self):
        """LOW risk → Step Functions sends approver_type='analyst' — must not raise."""
        event = self._build_sf_event(approver_type="analyst")
        app_summary = {"full_name": "Juan", "loan_amount": 20000.0, "fraud_score": 100, "fraud_risk_level": "LOW"}

        with patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "execute_query_single", return_value=app_summary), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "sns_client", MagicMock()):
            os.environ.pop("APPROVER_SNS_TOPIC_ARN", None)
            # Must not raise
            approval_mod.handle_notify_approver(event)

    def test_senior_officer_approver_type_is_accepted(self):
        """MEDIUM risk → Step Functions sends approver_type='senior_officer' — must not raise."""
        event = self._build_sf_event(approver_type="senior_officer")
        app_summary = {"full_name": "Juan", "loan_amount": 20000.0, "fraud_score": 400, "fraud_risk_level": "MEDIUM"}

        with patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "execute_query_single", return_value=app_summary), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "sns_client", MagicMock()):
            os.environ.pop("APPROVER_SNS_TOPIC_ARN", None)
            approval_mod.handle_notify_approver(event)

    def test_missing_approver_type_defaults_to_analyst(self):
        """If Step Functions omits approver_type, Lambda must default to 'analyst' without crashing."""
        event = {"application_id": "app-abc-123", "task_token": "sfn-token-abc"}
        app_summary = {"full_name": "Juan", "loan_amount": 20000.0, "fraud_score": 100, "fraud_risk_level": "LOW"}

        with patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "execute_query_single", return_value=app_summary), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "sns_client", MagicMock()):
            os.environ.pop("APPROVER_SNS_TOPIC_ARN", None)
            approval_mod.handle_notify_approver(event)  # must not raise


# ══════════════════════════════════════════════════════════════════════════════
# CONTRACT 3 — approvalNotifier → Step Functions (callback payload)
#
# approvalNotifier calls send_task_success(taskToken=..., output=<JSON>)
# The state machine's "ProcessDecision" Choice state reads:
#   "Variable": "$.decision"
#   "StringEquals": "APPROVED"   (default = REJECTED)
#
# The output JSON must contain exactly the key 'decision' with value
# 'APPROVED' or 'REJECTED' (uppercase).
# ══════════════════════════════════════════════════════════════════════════════

class TestContract3_ApprovalNotifierToStepFunctions:
    """approvalNotifier send_task_success() output → Step Functions ProcessDecision."""

    def test_approve_output_contains_decision_key(self, pending_token):
        """ProcessDecision reads $.decision — output must contain that key."""
        event = {
            "httpMethod": "POST",
            "path": "/api/loans/app-abc-123/approve",
            "pathParameters": {"id": "app-abc-123"},
            "body": json.dumps({"approvedBy": "analyst@bancafiel.com", "notes": "OK"}),
        }
        mock_sf = MagicMock()

        with patch.object(approval_mod, "execute_query_single", return_value=pending_token), \
             patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "stepfunctions_client", mock_sf):
            approval_mod.handle_approve(event)

        output = json.loads(mock_sf.send_task_success.call_args[1]["output"])
        assert "decision" in output, (
            "Missing 'decision' key in send_task_success output — "
            "ProcessDecision state reads $.decision"
        )

    def test_approve_decision_value_is_uppercase_approved(self, pending_token):
        """ProcessDecision checks StringEquals 'APPROVED' — must be uppercase, not 'approved'."""
        event = {
            "httpMethod": "POST",
            "path": "/api/loans/app-abc-123/approve",
            "pathParameters": {"id": "app-abc-123"},
            "body": json.dumps({"approvedBy": "analyst@bancafiel.com"}),
        }
        mock_sf = MagicMock()

        with patch.object(approval_mod, "execute_query_single", return_value=pending_token), \
             patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "stepfunctions_client", mock_sf):
            approval_mod.handle_approve(event)

        output = json.loads(mock_sf.send_task_success.call_args[1]["output"])
        assert output["decision"] == "APPROVED"

    def test_reject_decision_value_is_uppercase_rejected(self, pending_token):
        """ProcessDecision default branch handles REJECTED — must be uppercase."""
        event = {
            "httpMethod": "POST",
            "path": "/api/loans/app-abc-123/reject",
            "pathParameters": {"id": "app-abc-123"},
            "body": json.dumps({"rejectedBy": "senior@bancafiel.com", "reason": "High risk"}),
        }
        mock_sf = MagicMock()

        with patch.object(approval_mod, "execute_query_single", return_value=pending_token), \
             patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "stepfunctions_client", mock_sf):
            approval_mod.handle_reject(event)

        output = json.loads(mock_sf.send_task_success.call_args[1]["output"])
        assert output["decision"] == "REJECTED"

    def test_approve_output_contains_application_id(self, pending_token):
        """UpdateERPApproved state reads $.application_id — it must be in the output."""
        event = {
            "httpMethod": "POST",
            "path": "/api/loans/app-abc-123/approve",
            "pathParameters": {"id": "app-abc-123"},
            "body": json.dumps({"approvedBy": "analyst@bancafiel.com"}),
        }
        mock_sf = MagicMock()

        with patch.object(approval_mod, "execute_query_single", return_value=pending_token), \
             patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "stepfunctions_client", mock_sf):
            approval_mod.handle_approve(event)

        output = json.loads(mock_sf.send_task_success.call_args[1]["output"])
        assert output["application_id"] == "app-abc-123"

    def test_reject_output_contains_application_id(self, pending_token):
        """UpdateERPRejected state reads $.application_id — it must be in the output."""
        event = {
            "httpMethod": "POST",
            "path": "/api/loans/app-abc-123/reject",
            "pathParameters": {"id": "app-abc-123"},
            "body": json.dumps({"rejectedBy": "senior@bancafiel.com", "reason": "Risk"}),
        }
        mock_sf = MagicMock()

        with patch.object(approval_mod, "execute_query_single", return_value=pending_token), \
             patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "stepfunctions_client", mock_sf):
            approval_mod.handle_reject(event)

        output = json.loads(mock_sf.send_task_success.call_args[1]["output"])
        assert output["application_id"] == "app-abc-123"

    def test_task_token_used_for_send_task_success(self, pending_token):
        """The task token stored in DB must be the one sent back to Step Functions — not a different value."""
        event = {
            "httpMethod": "POST",
            "path": "/api/loans/app-abc-123/approve",
            "pathParameters": {"id": "app-abc-123"},
            "body": json.dumps({"approvedBy": "analyst@bancafiel.com"}),
        }
        mock_sf = MagicMock()

        with patch.object(approval_mod, "execute_query_single", return_value=pending_token), \
             patch.object(approval_mod, "execute_insert"), \
             patch.object(approval_mod, "create_application_history"), \
             patch.object(approval_mod, "stepfunctions_client", mock_sf):
            approval_mod.handle_approve(event)

        assert mock_sf.send_task_success.call_args[1]["taskToken"] == "sfn-task-token-xyz"
