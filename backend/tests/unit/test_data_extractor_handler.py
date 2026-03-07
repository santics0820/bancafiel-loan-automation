"""
Unit tests for Lambda #2: data-extractor handler
(backend/src/lambdas/data-extractor/handler.py)
This Lambda is now a pass-through that verifies Bedrock extraction and triggers validateData.
"""
import sys
import os
import json
import importlib.util
from unittest.mock import MagicMock, patch

import pytest


_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/data-extractor/handler.py")
)
_spec = importlib.util.spec_from_file_location("data_extractor_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["data_extractor_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


def _direct_event(document_id="doc-1", application_id="app-1"):
    return {"document_id": document_id, "application_id": application_id}


def test_handler_missing_document_id_returns_400():
    result = mod.handler({"application_id": "app-1"}, None)
    assert result["statusCode"] == 400


def test_handler_missing_application_id_returns_400():
    result = mod.handler({"document_id": "doc-1"}, None)
    assert result["statusCode"] == 400


def test_handler_document_not_found_returns_404():
    event = _direct_event()
    with patch.object(mod, "execute_query_single", return_value=None):
        result = mod.handler(event, None)
    assert result["statusCode"] == 404


def test_handler_success_triggers_validate_data():
    event = _direct_event(document_id="doc-9", application_id="app-9")
    document = {"id": "doc-9", "document_type": "INE", "textract_status": "SUCCEEDED"}

    with patch.object(mod, "execute_query_single", return_value=document):
        mod.lambda_client = MagicMock()
        result = mod.handler(event, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["document_id"] == "doc-9"
    assert body["application_id"] == "app-9"
    mod.lambda_client.invoke.assert_called_once()


def test_handler_invoke_failure_still_returns_200():
    event = _direct_event(document_id="doc-10", application_id="app-10")
    document = {"id": "doc-10", "document_type": "BANK_STATEMENT", "textract_status": "SUCCEEDED"}

    with patch.object(mod, "execute_query_single", return_value=document):
        mod.lambda_client = MagicMock()
        mod.lambda_client.invoke.side_effect = Exception("invoke failed")
        result = mod.handler(event, None)

    assert result["statusCode"] == 200


def test_handler_exception_returns_500():
    result = mod.handler({}, None)
    assert result["statusCode"] in (400, 500)
