"""
Unit tests for Lambda #2: data-extractor handler + helpers
"""
import sys
import os
import json
import importlib.util
from unittest.mock import MagicMock, patch


_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/data-extractor/handler.py")
)
_spec = importlib.util.spec_from_file_location("data_extractor_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["data_extractor_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


def _sns_event(job_id="job-1", status="SUCCEEDED"):
    return {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps({"JobId": job_id, "Status": status})
                }
            }
        ]
    }


def test_handler_status_failed_returns_400():
    event = _sns_event(status="FAILED")
    with patch.object(mod, "execute_query_single") as mock_lookup:
        result = mod.handler(event, None)
    assert result["statusCode"] == 400
    assert not mock_lookup.called


def test_handler_document_not_found_returns_404():
    event = _sns_event(status="SUCCEEDED")
    with patch.object(mod, "execute_query_single", return_value=None):
        result = mod.handler(event, None)
    assert result["statusCode"] == 404


def test_handler_success_saves_and_invokes_even_on_invoke_error():
    event = _sns_event(job_id="job-9", status="SUCCEEDED")
    document = {"id": "doc-9", "application_id": "app-9", "document_type": "INCOME_PROOF"}

    with patch.object(mod, "execute_query_single", return_value=document), \
         patch.object(mod, "get_textract_results", return_value=[]), \
         patch.object(mod, "parse_textract_blocks", return_value={
             "curp": {"value": "ABCD010203HDFXXX01", "confidence": 99}
         }), \
         patch.object(mod, "execute_insert") as mock_insert:
        mod.lambda_client = MagicMock()
        mod.lambda_client.invoke.side_effect = Exception("invoke failed")
        result = mod.handler(event, None)

    assert result["statusCode"] == 200
    assert mock_insert.called


def test_get_textract_results_paginates():
    mod.textract_client = MagicMock()
    mod.textract_client.get_document_text_detection.side_effect = [
        {"Blocks": [{"Id": "1"}], "NextToken": "next"},
        {"Blocks": [{"Id": "2"}]},
    ]
    blocks = mod.get_textract_results("job-1")
    assert blocks == [{"Id": "1"}, {"Id": "2"}]


def test_parse_textract_blocks_for_ine_and_address():
    ine_blocks = [
        {"BlockType": "LINE", "Text": "CURP ABCD010203HDFXXX01", "Confidence": 98},
        {"BlockType": "LINE", "Text": "NOMBRE JUAN PEREZ", "Confidence": 95},
        {"BlockType": "LINE", "Text": "DOMICILIO CALLE 1", "Confidence": 90},
        {"BlockType": "LINE", "Text": "FECHA NACIMIENTO 01/01/1990", "Confidence": 88},
    ]
    fields = mod.parse_textract_blocks(ine_blocks, "INE")
    assert fields["curp"]["value"] == "ABCD010203HDFXXX01"
    assert fields["full_name"]["value"] == "JUAN PEREZ"
    assert fields["address"]["value"].startswith("CALLE")
    assert fields["date_of_birth"]["value"] == "01/01/1990"

    addr_blocks = [
        {"BlockType": "LINE", "Text": "Calle Siempre Viva 123", "Confidence": 91}
    ]
    addr = mod.parse_textract_blocks(addr_blocks, "PROOF_OF_ADDRESS")
    assert addr["address"]["value"] == "Calle Siempre Viva 123"


def test_helpers_normalize_and_amount():
    assert mod.extract_curp("CURP ABCD010203HDFXXX01") == "ABCD010203HDFXXX01"
    assert mod.extract_after_label("NOMBRE: JUAN PEREZ", "NOMBRE") == "JUAN PEREZ"
    assert mod.extract_date("NACIMIENTO 01-01-1990") == "01-01-1990"
    assert mod.normalize_text("Razón   Social") == "RAZON SOCIAL"
    assert mod.extract_amount("$12.345,67") == "12345.67"


def test_next_line_amounts_and_periods():
    bank_lines = [
        {"text": "Saldo final", "confidence": 98.0},
        {"text": "$1,234.00", "confidence": 97.0},
        {"text": "Periodo", "confidence": 96.0},
        {"text": "01/01/2026 - 31/01/2026", "confidence": 95.0},
    ]
    bank_fields = mod.extract_bank_statement_fields(bank_lines)
    assert bank_fields["balance"]["value"] == "1234.00"
    assert bank_fields["period_start"]["value"] == "01/01/2026"
    assert bank_fields["period_end"]["value"] == "31/01/2026"

    income_lines = [
        {"text": "Total Neto", "confidence": 98.0},
        {"text": "$2,500.00", "confidence": 97.0},
        {"text": "Total Percepciones", "confidence": 96.0},
        {"text": "$3,000.00", "confidence": 95.0},
    ]
    income_fields = mod.extract_income_fields(income_lines)
    assert income_fields["net_income"]["value"] == "2500.00"
    assert income_fields["gross_income"]["value"] == "3000.00"
