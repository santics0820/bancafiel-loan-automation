"""
Unit tests for API routes: applications
(backend/src/api/routes/applications.py)

Run from the backend/ directory:
    python -m pytest tests/ -v --cov=src/api/routes/applications --cov-report=term-missing
"""
import sys
import os
import json
import importlib.util
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

# conftest.py injects utils.database, utils.logger, utils.response into sys.modules before this loads.

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/api/routes/applications.py")
)
_spec = importlib.util.spec_from_file_location("applications_route", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["applications_route"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


def _make_row(**kwargs):
    """Return a dict with all application columns defaulted."""
    defaults = {
        "id": "abc-123",
        "application_type": "LOAN",
        "loan_amount": 50000.0,
        "monthly_income": 15000.0,
        "existing_debt": 0.0,
        "requested_date": datetime(2026, 2, 1, 10, 0, 0),
        "status": "PENDING",
        "fraud_score": 0.1,
        "credit_score": 700,
        "fraud_risk_level": "LOW",
        "credit_recommendation": "APPROVE",
        "applicant_name": "Juan Pérez",
        "applicant_email": "juan@example.com",
        "full_name": "Juan Pérez",
        "email": "juan@example.com",
        "curp": "PERJ900101HDFXXX01",
        "phone": "5512345678",
        "address": "Calle Falsa 123",
    }
    defaults.update(kwargs)
    return defaults


class TestListApplications:
    def test_returns_applications_for_default_status(self):
        row = _make_row()
        event = {"queryStringParameters": None}

        with patch.object(mod, "execute_query", return_value=[row]) as mock_q:
            result = mod.list_applications(event, context=MagicMock())

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["total"] == 1
        assert body["applications"][0]["id"] == "abc-123"
        assert body["applications"][0]["status"] == "pending"
        assert body["applications"][0]["loanAmount"] == 50000.0
        # Default status is "pending" → query should use "PENDING"
        query_params = mock_q.call_args[0][1]
        assert query_params == ("PENDING",)

    def test_filters_by_status_param(self):
        event = {"queryStringParameters": {"status": "approved"}}

        with patch.object(mod, "execute_query", return_value=[]) as mock_q:
            result = mod.list_applications(event, context=MagicMock())

        assert result["statusCode"] == 200
        assert mock_q.call_args[0][1] == ("APPROVED",)

    def test_null_optional_fields_handled(self):
        row = _make_row(monthly_income=None, fraud_score=None, fraud_risk_level=None)
        event = {"queryStringParameters": None}

        with patch.object(mod, "execute_query", return_value=[row]):
            result = mod.list_applications(event, context=MagicMock())

        body = json.loads(result["body"])
        app = body["applications"][0]
        assert app["monthlyIncome"] is None
        assert app["fraudScore"] is None
        assert app["fraudRiskLevel"] is None

    def test_returns_500_on_db_error(self):
        event = {"queryStringParameters": None}

        with patch.object(mod, "execute_query", side_effect=Exception("DB down")):
            result = mod.list_applications(event, context=MagicMock())

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Failed to retrieve applications" in body.get("message", body.get("error", ""))


class TestGetApplication:
    def test_returns_full_application_detail(self):
        app_row = _make_row()
        event = {"pathParameters": {"id": "abc-123"}}

        with patch.object(mod, "execute_query_single", return_value=app_row), \
             patch.object(mod, "execute_query", side_effect=[
                 [{"document_type": "INE", "s3_bucket": "my-bucket", "s3_key": "applications/abc-123/ine.pdf"}],
                 [{"action": "submitted", "actor": "system", "notes": "ok", "created_at": datetime(2026, 2, 1)}],
                 [{"field_name": "curp", "field_value": "PERJ900101HDFXXX01"}],
             ]):
            result = mod.get_application(event, context=MagicMock())

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["id"] == "abc-123"
        assert body["curp"] == "PERJ900101HDFXXX01"
        assert len(body["documents"]) == 1
        assert body["documents"][0]["type"] == "INE"
        assert body["extractedData"]["curp"] == "PERJ900101HDFXXX01"
        assert len(body["history"]) == 1

    def test_returns_404_when_not_found(self):
        event = {"pathParameters": {"id": "missing-id"}}

        with patch.object(mod, "execute_query_single", return_value=None):
            result = mod.get_application(event, context=MagicMock())

        assert result["statusCode"] == 404

    def test_returns_500_on_db_error(self):
        event = {"pathParameters": {"id": "abc-123"}}

        with patch.object(mod, "execute_query_single", side_effect=Exception("timeout")):
            result = mod.get_application(event, context=MagicMock())

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Failed to retrieve application" in body.get("message", body.get("error", ""))


class TestSubmitApplication:
    def _make_event(self, body_dict):
        return {"body": json.dumps(body_dict)}

    def test_creates_application_and_returns_201(self):
        event = self._make_event({
            "applicantName": "Juan Pérez",
            "applicantEmail": "juan@example.com",
            "loanAmount": 50000,
            "applicationType": "LOAN",
        })

        with patch.object(mod, "execute_query", return_value=[{"id": "new-id"}]), \
             patch.object(mod, "s3_client") as mock_s3:
            mock_s3.generate_presigned_url.return_value = "https://s3.example.com/presigned"
            result = mod.submit_application(event, context=MagicMock())

        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["applicationId"] == "new-id"
        assert body["status"] == "pending"

    def test_returns_400_for_missing_required_fields(self):
        event = self._make_event({
            "applicantName": "Juan Pérez",
            # missing applicantEmail, loanAmount, applicationType
        })

        result = mod.submit_application(event, context=MagicMock())

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "Missing required fields" in body.get("message", body.get("error", ""))

    def test_returns_400_for_invalid_application_type(self):
        event = self._make_event({
            "applicantName": "Juan Pérez",
            "applicantEmail": "juan@example.com",
            "loanAmount": 10000,
            "applicationType": "MORTGAGE",
        })

        with patch.object(mod, "execute_query", return_value=[{"id": "x"}]):
            result = mod.submit_application(event, context=MagicMock())

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "applicationType" in body.get("message", body.get("error", ""))

    def test_returns_500_on_db_error(self):
        event = self._make_event({
            "applicantName": "Juan Pérez",
            "applicantEmail": "juan@example.com",
            "loanAmount": 10000,
            "applicationType": "LOAN",
        })

        with patch.object(mod, "execute_query", side_effect=Exception("DB error")):
            result = mod.submit_application(event, context=MagicMock())

        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Failed to submit application" in body.get("message", body.get("error", ""))

    def test_credit_card_type_accepted(self):
        event = self._make_event({
            "applicantName": "Ana López",
            "applicantEmail": "ana@example.com",
            "loanAmount": 20000,
            "applicationType": "CREDIT_CARD",
        })

        with patch.object(mod, "execute_query", return_value=[{"id": "cc-id"}]):
            result = mod.submit_application(event, context=MagicMock())

        assert result["statusCode"] == 201
