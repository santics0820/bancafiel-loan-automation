"""
Unit tests for Lambda #4: fraud-detector
(backend/src/lambdas/fraud-detector/handler.py)

Coverage targets:
  - score_to_risk()           — all three risk bands + boundary values
  - rule_based_fraud_score()  — each scoring rule individually
  - handler()                 — 404, 200, Step Functions trigger, 500

Run from the backend/ directory:
    pytest tests/ -v --cov=src/lambdas/fraud-detector --cov-report=term-missing
"""
import sys
import os
import json
import importlib.util
from unittest.mock import patch, MagicMock

import pytest

# ── Load the handler module via importlib ─────────────────────────────────────
# conftest.py has already injected mock utils into sys.modules, so the
# `from utils.xxx import ...` statements inside the handler resolve correctly.

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/fraud-detector/handler.py")
)
_spec = importlib.util.spec_from_file_location("fraud_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["fraud_handler"] = mod

# Patch boto3.client so the module-level client objects are MagicMocks
with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def app_data():
    """Minimal application record as returned by execute_query_single."""
    return {
        "id": "app-001",
        "customer_id": "cust-001",
        "loan_amount": 20_000.0,   # DTI = 20k/(10k*12) ≈ 0.17 — below both DTI thresholds
        "monthly_income": 10_000.0,
        "curp": "ABCD123456HDFXXX01",
        "email": "juan@example.com",
        "phone": "5551234567",
        "full_name": "Juan Perez",
    }


@pytest.fixture
def lambda_context():
    ctx = MagicMock()
    ctx.function_name = "bancafiel-detectFraud-dev"
    ctx.aws_request_id = "test-request-id"
    return ctx


# ── Tests: score_to_risk() ────────────────────────────────────────────────────

class TestScoreToRisk:
    """Verify the three risk bands and their exact boundary values."""

    def test_low_risk_at_100(self):
        assert mod.score_to_risk(100) == "LOW"

    def test_low_risk_at_299(self):
        # 299 is the last value before MEDIUM starts
        assert mod.score_to_risk(299) == "LOW"

    def test_medium_risk_at_300(self):
        # Boundary: 300 is the first MEDIUM value
        assert mod.score_to_risk(300) == "MEDIUM"

    def test_medium_risk_at_699(self):
        # 699 is the last value before HIGH starts
        assert mod.score_to_risk(699) == "MEDIUM"

    def test_high_risk_at_700(self):
        # Boundary: 700 is the first HIGH value
        assert mod.score_to_risk(700) == "HIGH"

    def test_high_risk_at_1000(self):
        assert mod.score_to_risk(1000) == "HIGH"


# ── Tests: rule_based_fraud_score() ──────────────────────────────────────────

class TestRuleBasedFraudScore:
    """Each fraud rule is tested in isolation."""

    def test_clean_profile_is_low_risk(self, app_data):
        """Low loan, normal DTI, no duplicates → base score 100 → LOW."""
        with patch.object(mod, "count_duplicate_applications", return_value=0):
            score, risk, reasons = mod.rule_based_fraud_score(app_data)

        assert risk == "LOW"
        assert score == 100
        assert reasons == []

    def test_elevated_dti_adds_150_points(self, app_data):
        """DTI between 0.40 and 0.60 triggers the elevated-DTI rule."""
        # DTI = 55_000 / (10_000 * 12) ≈ 0.458  →  +150
        app_data["loan_amount"] = 55_000.0
        with patch.object(mod, "count_duplicate_applications", return_value=0):
            score, _, reasons = mod.rule_based_fraud_score(app_data)

        assert "elevated_debt_to_income_ratio" in reasons
        assert score == 250  # 100 base + 150

    def test_high_dti_adds_300_points(self, app_data):
        """DTI > 0.60 triggers the high-DTI rule."""
        # DTI = 90_000 / 120_000 = 0.75  →  +300
        app_data["loan_amount"] = 90_000.0
        with patch.object(mod, "count_duplicate_applications", return_value=0):
            score, risk, reasons = mod.rule_based_fraud_score(app_data)

        assert "high_debt_to_income_ratio" in reasons
        assert score == 400  # 100 + 300
        assert risk == "MEDIUM"

    def test_high_loan_amount_adds_200_points(self, app_data):
        """Loan amount > 100,000 MXN adds 200 points."""
        app_data["loan_amount"] = 110_000.0
        app_data["monthly_income"] = 0  # skip DTI rule to isolate this one
        with patch.object(mod, "count_duplicate_applications", return_value=0):
            score, _, reasons = mod.rule_based_fraud_score(app_data)

        assert "high_loan_amount" in reasons
        assert score == 300  # 100 + 200

    def test_duplicate_applications_adds_400_points(self, app_data):
        """A pending duplicate application adds 400 points."""
        app_data["monthly_income"] = 0  # isolate: skip DTI
        app_data["loan_amount"] = 50_000.0  # < 100k: no high-amount rule
        with patch.object(mod, "count_duplicate_applications", return_value=1):
            score, risk, reasons = mod.rule_based_fraud_score(app_data)

        assert any("duplicate_applications_found" in r for r in reasons)
        assert score == 500  # 100 + 400
        assert risk == "MEDIUM"

    def test_score_capped_at_1000(self, app_data):
        """Stacking all rules must not exceed the 1000 maximum."""
        app_data["loan_amount"] = 200_000.0  # high amount + very high DTI
        with patch.object(mod, "count_duplicate_applications", return_value=3):
            score, _, _ = mod.rule_based_fraud_score(app_data)

        assert score == 1000

    def test_zero_income_skips_dti_rule(self, app_data):
        """Income of 0 must not cause ZeroDivisionError and must skip DTI rules."""
        app_data["monthly_income"] = 0
        app_data["loan_amount"] = 50_000.0
        with patch.object(mod, "count_duplicate_applications", return_value=0):
            score, _, reasons = mod.rule_based_fraud_score(app_data)

        assert "high_debt_to_income_ratio" not in reasons
        assert "elevated_debt_to_income_ratio" not in reasons
        assert score == 100


# ── Tests: handler() ─────────────────────────────────────────────────────────

class TestHandler:
    """Integration-level tests for the Lambda entry point."""

    def test_returns_404_when_application_not_found(self, lambda_context):
        event = {"application_id": "missing-id"}
        with patch.object(mod, "execute_query_single", return_value=None):
            result = mod.handler(event, lambda_context)

        assert result["statusCode"] == 404

    def test_returns_200_with_fraud_score_on_success(self, app_data, lambda_context):
        """Happy path — LOW risk, no Step Functions ARN configured."""
        event = {"application_id": "app-001"}
        os.environ.pop("LOAN_WORKFLOW_ARN", None)

        with patch.object(mod, "execute_query_single", return_value=app_data), \
             patch.object(mod, "execute_insert"), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "run_fraud_detection", return_value=(100, "LOW", [])), \
             patch.object(mod, "count_duplicate_applications", return_value=0):
            result = mod.handler(event, lambda_context)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["fraud_score"] == 100
        assert body["risk_level"] == "LOW"
        assert body["reasons"] == []

    def test_triggers_step_functions_when_arn_is_set(self, app_data, lambda_context):
        """When LOAN_WORKFLOW_ARN is in env, start_execution must be called."""
        event = {"application_id": "app-001"}
        mock_sf = MagicMock()

        with patch.object(mod, "execute_query_single", return_value=app_data), \
             patch.object(mod, "execute_insert"), \
             patch.object(mod, "create_application_history"), \
             patch.object(mod, "run_fraud_detection", return_value=(750, "HIGH", ["high_dti"])), \
             patch.object(mod, "count_duplicate_applications", return_value=0), \
             patch.object(mod, "stepfunctions_client", mock_sf), \
             patch.dict(os.environ, {"LOAN_WORKFLOW_ARN": "arn:aws:states:us-east-1:123:stateMachine:test"}):
            result = mod.handler(event, lambda_context)

        assert result["statusCode"] == 200
        mock_sf.start_execution.assert_called_once()
        # Verify the execution input contains expected fields
        call_kwargs = mock_sf.start_execution.call_args[1]
        payload = json.loads(call_kwargs["input"])
        assert payload["fraud_risk_level"] == "HIGH"
        assert payload["application_id"] == "app-001"

    def test_returns_500_on_unexpected_exception(self, lambda_context):
        """Any uncaught exception must return 500, not raise."""
        event = {"application_id": "app-001"}
        with patch.object(mod, "execute_query_single", side_effect=Exception("DB connection failed")):
            result = mod.handler(event, lambda_context)

        assert result["statusCode"] == 500
