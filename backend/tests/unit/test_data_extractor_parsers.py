"""
Unit tests for Lambda #2: data-extractor OCR parsers
(backend/src/lambdas/data-extractor/handler.py)

Covers extract_bank_statement_fields() and extract_income_fields()
with inline inputs and fixture-based end-to-end pairs.

Run from the backend/ directory:
    python -m pytest tests/ -v --cov=src/lambdas/data-extractor --cov-report=term-missing
"""
import importlib.util
import os
import sys
import json
from unittest.mock import MagicMock, patch


_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/lambdas/data-extractor/handler.py")
)
_spec = importlib.util.spec_from_file_location("data_extractor_handler", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["data_extractor_handler"] = mod

with patch("boto3.client", return_value=MagicMock()):
    _spec.loader.exec_module(mod)


def make_lines(*texts):
    return [{"text": t, "confidence": 98.0} for t in texts]


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "../fixtures", name)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_fixture_pairs():
    fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../fixtures"))
    if not os.path.isdir(fixtures_dir):
        return []
    pairs = []
    for filename in os.listdir(fixtures_dir):
        if not filename.endswith("_lines.json"):
            continue
        expected = filename.replace("_lines.json", "_expected.json")
        if os.path.exists(os.path.join(fixtures_dir, expected)):
            pairs.append((filename, expected))
    return pairs


def test_extract_bank_statement_fields_basic():
    lines = make_lines(
        "BBVA",
        "CLABE 012345678901234567",
        "Cuenta 1234567890",
        "RFC ABCD010203ABC",
        "Periodo 01/01/2026 - 31/01/2026",
        "Saldo final $12,345.67",
        "Saldo promedio $10,000.00",
        "Depositos $25,000.00",
        "Retiros $5,000.00",
    )

    fields = mod.extract_bank_statement_fields(lines)

    assert fields["bank_name"]["value"] == "BBVA"
    assert fields["clabe"]["value"] == "012345678901234567"
    assert fields["account_number"]["value"] == "1234567890"
    assert fields["rfc"]["value"] == "ABCD010203ABC"
    assert fields["period_start"]["value"] == "01/01/2026"
    assert fields["period_end"]["value"] == "31/01/2026"
    assert fields["balance"]["value"] == "12345.67"
    assert fields["average_balance"]["value"] == "10000.00"
    assert fields["total_deposits"]["value"] == "25000.00"
    assert fields["total_withdrawals"]["value"] == "5000.00"


def test_extract_bank_statement_fields_variants():
    lines = make_lines(
        "BBVA México",
        "CLABE Interbancaria: 012345678901234567",
        "No. Cuenta: 123456789012",
        "RFC ABCD010203ABC",
        "Periodo del 01-01-2026 al 31-01-2026",
        "Saldo actual $12.345,67",
        "Saldo promedio $10.000,00",
        "Abonos $1.234,56",
        "Cargos $987,65",
    )

    fields = mod.extract_bank_statement_fields(lines)

    assert fields["bank_name"]["value"] == "BBVA MEXICO"
    assert fields["clabe"]["value"] == "012345678901234567"
    assert fields["account_number"]["value"] == "123456789012"
    assert fields["period_start"]["value"] == "01-01-2026"
    assert fields["period_end"]["value"] == "31-01-2026"
    assert fields["balance"]["value"] == "12345.67"
    assert fields["average_balance"]["value"] == "10000.00"
    assert fields["total_deposits"]["value"] == "1234.56"
    assert fields["total_withdrawals"]["value"] == "987.65"


def test_extract_income_fields_basic():
    lines = make_lines(
        "Empresa ACME SA DE CV",
        "RFC XAXX010101000",
        "Periodo 01/02/2026 - 15/02/2026",
        "Quincenal",
        "Total Neto $8,500.50",
        "Total Percepciones $10,000.00",
    )

    fields = mod.extract_income_fields(lines)

    assert fields["employer_name"]["value"] == "ACME SA DE CV"
    assert fields["rfc"]["value"] == "XAXX010101000"
    assert fields["payment_frequency"]["value"] == "QUINCENAL"
    assert fields["period_start"]["value"] == "01/02/2026"
    assert fields["period_end"]["value"] == "15/02/2026"
    assert fields["net_income"]["value"] == "8500.50"
    assert fields["gross_income"]["value"] == "10000.00"


def test_extract_income_fields_variants():
    lines = make_lines(
        "Razón social: ACME SA DE CV",
        "RFC XAXX010101000",
        "Periodo del 01-02-2026 al 07-02-2026",
        "Semanal",
        "Neto a pagar $1.234,00",
        "Percepciones $2,000.00",
    )

    fields = mod.extract_income_fields(lines)

    assert fields["employer_name"]["value"] == "ACME SA DE CV"
    assert fields["rfc"]["value"] == "XAXX010101000"
    assert fields["payment_frequency"]["value"] == "SEMANAL"
    assert fields["period_start"]["value"] == "01-02-2026"
    assert fields["period_end"]["value"] == "07-02-2026"
    assert fields["net_income"]["value"] == "1234.00"
    assert fields["gross_income"]["value"] == "2000.00"


def test_fixture_pairs_end_to_end():
    pairs = iter_fixture_pairs()
    if not pairs:
        return

    for lines_name, expected_name in pairs:
        lines = load_fixture(lines_name)
        expected = load_fixture(expected_name)

        document_type = expected.get("document_type")
        fields = expected.get("fields")

        if document_type == "BANK_STATEMENT":
            actual = mod.extract_bank_statement_fields(lines)
        elif document_type == "INCOME_PROOF":
            actual = mod.extract_income_fields(lines)
        else:
            raise AssertionError(f"Unsupported document_type in {expected_name}: {document_type}")

        assert actual == fields
