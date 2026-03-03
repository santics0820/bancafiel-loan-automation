"""
Unit tests for Lambda #1: document-processor
(backend/src/lambdas/document-processor/handler.py)
Uses Claude Sonnet 4.5 on Amazon Bedrock for OCR extraction.
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


def _bedrock_response(fields):
    """Build a mock Bedrock invoke_model response returning JSON fields."""
    body_bytes = json.dumps(fields).encode()
    mock_stream = MagicMock()
    mock_stream.read.return_value = json.dumps({
        "content": [{"type": "text", "text": json.dumps(fields)}]
    }).encode()
    return {"body": mock_stream}


def test_handler_happy_path_calls_bedrock_and_saves_doc(lambda_context):
    os.environ["VALIDATE_DATA_FUNCTION"] = "bancafiel-validateData-dev"
    os.environ["BEDROCK_MODEL_ID"] = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

    event = _s3_event("applications/app-001/ine.pdf", size=456)

    mock_body = MagicMock()
    mock_body.read.return_value = json.dumps({
        "Records": [{"s3": {"bucket": {"name": "b"}, "object": {"key": "k", "size": 1}}}]
    }).encode()

    s3_get_response = {"Body": MagicMock()}
    s3_get_response["Body"].read.return_value = b"fake-pdf-bytes"

    bedrock_resp = {
        "body": MagicMock()
    }
    bedrock_resp["body"].read.return_value = json.dumps({
        "content": [{"type": "text", "text": json.dumps({
            "full_name": "Juan Perez",
            "curp": "PERJ850315HDFRN01"
        })}]
    }).encode()

    mod.s3_client.get_object.return_value = s3_get_response
    mod.bedrock_client.invoke_model.return_value = bedrock_resp

    with patch.object(mod, "execute_insert", return_value=[{"id": "doc-001"}]) as mock_insert, \
         patch.object(mod, "save_extracted_data") as mock_save:
        mod.lambda_client = MagicMock()
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    assert mod.bedrock_client.invoke_model.called
    assert mock_insert.called

    # First call is the INSERT — check its params
    first_call_args = mock_insert.call_args_list[0][0]
    _, params = first_call_args
    assert params[0] == "app-001"   # application_id
    assert params[1] == "INE"       # document_type
    assert params[2] == "incoming-bucket"
    assert params[3] == "applications/app-001/ine.pdf"
    assert params[4] == 456         # file_size


def test_handler_invalid_key_skips_bedrock_and_db(lambda_context):
    event = _s3_event("badfile.pdf")
    mod.bedrock_client.invoke_model.reset_mock()

    with patch.object(mod, "execute_insert") as mock_insert:
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    assert not mod.bedrock_client.invoke_model.called
    assert not mock_insert.called


def test_determine_document_type_defaults_income():
    assert mod.determine_document_type("applications/app-001/unknown.pdf") == "INCOME_PROOF"


def test_handler_bedrock_failure_still_inserts_pending(lambda_context):
    os.environ["VALIDATE_DATA_FUNCTION"] = "bancafiel-validateData-dev"

    event = _s3_event("applications/app-009/bank.pdf", size=999)

    s3_get_response = {"Body": MagicMock()}
    s3_get_response["Body"].read.return_value = b"fake-pdf-bytes"
    mod.s3_client.get_object.return_value = s3_get_response
    mod.bedrock_client.invoke_model.side_effect = Exception("bedrock unavailable")

    with patch.object(mod, "execute_insert", return_value=[{"id": "doc-009"}]) as mock_insert:
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200
    assert mock_insert.called
    _, params = mock_insert.call_args[0]
    assert params[0] == "app-009"
    assert params[1] == "BANK_STATEMENT"
    assert params[6] == "FAILED"   # status when Bedrock fails

    mod.bedrock_client.invoke_model.side_effect = None


def test_determine_document_type_variants():
    assert mod.determine_document_type("applications/app-001/ife.pdf") == "INE"
    assert mod.determine_document_type("applications/app-001/comprobante.pdf") == "PROOF_OF_ADDRESS"
    assert mod.determine_document_type("applications/app-001/estado_cuenta.pdf") == "BANK_STATEMENT"
    assert mod.determine_document_type("applications/app-001/nomina.pdf") == "INCOME_PROOF"


def test_handler_database_insert_failure_returns_200(lambda_context):
    os.environ["VALIDATE_DATA_FUNCTION"] = "bancafiel-validateData-dev"

    event = _s3_event("applications/app-010/ine.pdf", size=321)

    s3_get_response = {"Body": MagicMock()}
    s3_get_response["Body"].read.return_value = b"fake-pdf-bytes"
    mod.s3_client.get_object.return_value = s3_get_response

    bedrock_resp = {"body": MagicMock()}
    bedrock_resp["body"].read.return_value = json.dumps({
        "content": [{"type": "text", "text": json.dumps({"full_name": "Test"})}]
    }).encode()
    mod.bedrock_client.invoke_model.return_value = bedrock_resp

    with patch.object(mod, "execute_insert", side_effect=Exception("db down")):
        result = mod.handler(event, lambda_context)

    assert result["statusCode"] == 200


def test_handler_exception_returns_500(lambda_context):
    result = mod.handler({}, lambda_context)
    assert result["statusCode"] == 500


def test_extract_with_bedrock_parses_json_response():
    bedrock_resp = {"body": MagicMock()}
    bedrock_resp["body"].read.return_value = json.dumps({
        "content": [{"type": "text", "text": json.dumps({
            "full_name": "Maria Lopez",
            "curp": "LOPM900101MDFPXX01",
            "date_of_birth": "01/01/1990"
        })}]
    }).encode()
    mod.bedrock_client.invoke_model.return_value = bedrock_resp

    import base64
    fields = mod.extract_with_bedrock(base64.b64encode(b"fake").decode(), "INE")

    assert fields["full_name"]["value"] == "Maria Lopez"
    assert fields["curp"]["value"] == "LOPM900101MDFPXX01"
    assert fields["full_name"]["confidence"] == 99.0
