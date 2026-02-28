"""
Unit tests for Lambda #3: data-validator
(backend/src/lambdas/data-validator/handler.py)
"""
import sys
import os
import json
import importlib.util
from unittest.mock import MagicMock, patch

import pytest


_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/data-validator/handler.py")
)
_spec = importlib.util.spec_from_file_location("data_validator_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["data_validator_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


@pytest.fixture
def lambda_context():
    ctx = MagicMock()
    ctx.function_name = "bancafiel-validateData-dev"
    ctx.aws_request_id = "test-request-id"
    return ctx


def test_invalid_curp_sets_error_and_returns_200(lambda_context):
    event = {"document_id": "doc-1", "application_id": "app-1"}
    extracted_fields = [
        {"field_name": "curp", "field_value": "INVALID", "confidence": 90},
        {"field_name": "full_name", "field_value": "Juan Perez", "confidence": 95},
    ]

    with patch.object(mod, "execute_query", side_effect=[extracted_fields, [{"id": "cust-1"}]]), \
         patch.object(mod, "execute_query_single", return_value=None), \
         patch.object(mod, "execute_insert"), \
         patch.object(mod, "create_application_history"):
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["is_valid"] is False
    assert "Invalid CURP format" in body["errors"]
    mod.lambda_client.invoke.assert_called_once()


def test_missing_curp_adds_warning(lambda_context):
    event = {"document_id": "doc-2", "application_id": "app-2"}
    extracted_fields = [
        {"field_name": "full_name", "field_value": "Maria Lopez", "confidence": 93},
    ]

    with patch.object(mod, "execute_query", return_value=extracted_fields), \
         patch.object(mod, "execute_query_single") as mock_lookup, \
         patch.object(mod, "execute_insert"), \
         patch.object(mod, "create_application_history"):
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "CURP not found in document" in body["warnings"]
    assert not mock_lookup.called
    mod.lambda_client.invoke.assert_called_once()


def test_existing_customer_name_mismatch_warns(lambda_context):
    event = {"document_id": "doc-3", "application_id": "app-3"}
    extracted_fields = [
        {"field_name": "curp", "field_value": "ABCD010203HDFXXX01", "confidence": 98},
        {"field_name": "full_name", "field_value": "Ana Gomez", "confidence": 90},
    ]
    existing_customer = {"id": "cust-9", "full_name": "Carlos Ramirez"}

    with patch.object(mod, "execute_query", return_value=extracted_fields), \
         patch.object(mod, "execute_query_single", return_value=existing_customer), \
         patch.object(mod, "execute_insert") as mock_update, \
         patch.object(mod, "create_application_history"):
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert any("Name mismatch" in w for w in body["warnings"])
    assert mock_update.called
    mod.lambda_client.invoke.assert_called_once()


def test_valid_curp_creates_customer_and_links_application(lambda_context):
    event = {"document_id": "doc-4", "application_id": "app-4"}
    extracted_fields = [
        {"field_name": "curp", "field_value": "ABCD010203HDFXXX01", "confidence": 98},
        {"field_name": "full_name", "field_value": "Ana Gomez", "confidence": 90},
        {"field_name": "address", "field_value": "Calle 123", "confidence": 85},
        {"field_name": "date_of_birth", "field_value": "01/01/1990", "confidence": 80},
    ]

    with patch.object(mod, "execute_query", side_effect=[extracted_fields, [{"id": "cust-1"}]]), \
         patch.object(mod, "execute_query_single", return_value=None), \
         patch.object(mod, "execute_insert") as mock_update, \
         patch.object(mod, "create_application_history") as mock_history:
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["is_valid"] is True
    assert body["customer_id"] == "cust-1"
    assert mock_update.called
    assert mock_history.called
    mod.lambda_client.invoke.assert_called_once()


def test_missing_name_adds_warning(lambda_context):
    event = {"document_id": "doc-5", "application_id": "app-5"}
    extracted_fields = [
        {"field_name": "curp", "field_value": "ABCD010203HDFXXX01", "confidence": 98},
    ]

    with patch.object(mod, "execute_query", side_effect=[extracted_fields, [{"id": "cust-5"}]]), \
         patch.object(mod, "execute_query_single", return_value=None), \
         patch.object(mod, "execute_insert"), \
         patch.object(mod, "create_application_history"):
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "Name not extracted from document" in body["warnings"]
    mod.lambda_client.invoke.assert_called_once()


def test_detect_fraud_uses_env_override(lambda_context):
    event = {"document_id": "doc-6", "application_id": "app-6"}
    extracted_fields = [
        {"field_name": "curp", "field_value": "ABCD010203HDFXXX01", "confidence": 98},
        {"field_name": "full_name", "field_value": "Ana Gomez", "confidence": 90},
    ]

    os.environ["DETECT_FRAUD_FUNCTION"] = "bancafiel-detectFraud-test"

    with patch.object(mod, "execute_query", return_value=extracted_fields), \
         patch.object(mod, "execute_query_single", return_value={"id": "cust-2", "full_name": "Ana Gomez"}), \
         patch.object(mod, "execute_insert"), \
         patch.object(mod, "create_application_history"):
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    mod.lambda_client.invoke.assert_called_once()
    args, kwargs = mod.lambda_client.invoke.call_args
    assert kwargs["FunctionName"] == "bancafiel-detectFraud-test"
    del os.environ["DETECT_FRAUD_FUNCTION"]


def test_name_similarity_helper():
    assert mod.names_similar("Ana Maria", "Ana Maria") is True
    assert mod.names_similar("Ana Maria", "Ana M.") is False
    assert mod.names_similar("Ana Maria", "Carlos Perez") is False
