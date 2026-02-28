"""
Unit tests for Lambda #1: document-processor
(backend/src/lambdas/document-processor/handler.py)
"""
import sys
import os
import json
import importlib.util
from unittest.mock import MagicMock, patch

import pytest


_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/document-processor/handler.py")
)
_spec = importlib.util.spec_from_file_location("document_processor_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["document_processor_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


def _s3_event(key, size=123, bucket="incoming-bucket"):
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": key, "size": size},
                }
            }
        ]
    }


@pytest.fixture
def lambda_context():
    ctx = MagicMock()
    ctx.function_name = "bancafiel-processDocument-dev"
    ctx.aws_request_id = "test-request-id"
    return ctx


def test_handler_happy_path_starts_textract_and_saves_doc(lambda_context):
    os.environ["TEXTRACT_SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123:textract"
    os.environ["TEXTRACT_ROLE_ARN"] = "arn:aws:iam::123:role/textract"

    event = _s3_event("applications/app-001/ine.pdf", size=456)

    mod.textract_client.start_document_text_detection.return_value = {"JobId": "job-123"}

    with patch.object(mod, "execute_insert") as mock_insert:
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200

    mod.textract_client.start_document_text_detection.assert_called_once()

    assert mock_insert.called
    _, params = mock_insert.call_args[0]
    assert params[0] == "app-001"
    assert params[1] == "INE"
    assert params[2] == "incoming-bucket"
    assert params[3] == "applications/app-001/ine.pdf"
    assert params[4] == 456
    assert params[5] == "job-123"
    assert params[6] == "IN_PROGRESS"


def test_handler_invalid_key_skips_textract_and_db(lambda_context):
    event = _s3_event("badfile.pdf")
    mod.textract_client.start_document_text_detection.reset_mock()

    with patch.object(mod, "execute_insert") as mock_insert:
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["job_id"] is None

    assert not mod.textract_client.start_document_text_detection.called
    assert not mock_insert.called


def test_determine_document_type_defaults_income():
    assert mod.determine_document_type("applications/app-001/unknown.pdf") == "INCOME_PROOF"


def test_handler_textract_failure_still_inserts_pending(lambda_context):
    os.environ["TEXTRACT_SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123:textract"
    os.environ["TEXTRACT_ROLE_ARN"] = "arn:aws:iam::123:role/textract"

    event = _s3_event("applications/app-009/bank.pdf", size=999)
    mod.textract_client.start_document_text_detection.side_effect = Exception("boom")

    with patch.object(mod, "execute_insert") as mock_insert:
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    assert mock_insert.called
    _, params = mock_insert.call_args[0]
    assert params[0] == "app-009"
    assert params[1] == "BANK_STATEMENT"
    assert params[5] is None
    assert params[6] == "PENDING"


def test_determine_document_type_variants():
    assert mod.determine_document_type("applications/app-001/ife.pdf") == "INE"
    assert mod.determine_document_type("applications/app-001/comprobante.pdf") == "PROOF_OF_ADDRESS"
    assert mod.determine_document_type("applications/app-001/estado_cuenta.pdf") == "BANK_STATEMENT"
    assert mod.determine_document_type("applications/app-001/nomina.pdf") == "INCOME_PROOF"


def test_handler_database_insert_failure_returns_200(lambda_context):
    os.environ["TEXTRACT_SNS_TOPIC_ARN"] = "arn:aws:sns:us-east-1:123:textract"
    os.environ["TEXTRACT_ROLE_ARN"] = "arn:aws:iam::123:role/textract"

    event = _s3_event("applications/app-010/ine.pdf", size=321)
    mod.textract_client.start_document_text_detection.return_value = {"JobId": "job-999"}

    with patch.object(mod, "execute_insert", side_effect=Exception("db down")):
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200


def test_handler_exception_returns_500(lambda_context):
    result = mod.handler({}, lambda_context)
    assert result["statusCode"] == 500
