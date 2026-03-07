"""
Unit tests for API route: GET /api/fraud
(backend/src/api/routes/fraud.py)

Run from the backend/ directory:
    python -m pytest tests/unit/test_fraud_route.py -v --cov=src/api/routes/fraud --cov-report=term-missing
"""
import sys
import os
import json
import importlib.util
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock

import pytest

_HANDLER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/api/routes/fraud.py")
)
_spec = importlib.util.spec_from_file_location("fraud_route", _HANDLER_PATH)
mod = importlib.util.module_from_spec(_spec)
sys.modules["fraud_route"] = mod
_spec.loader.exec_module(mod)


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_flagged_row(**kwargs):
    defaults = {
        "application_id": "aaaa1111-bbbb-cccc-dddd-eeeeeeeeeeee",
        "fraud_score": 750,
        "risk_level": "HIGH",
        "fraud_reasons": json.dumps(["high_loan_amount", "duplicate_applications_found"]),
        "duplicate_applications_count": 2,
        "created_at": datetime(2026, 2, 28, 10, 0, 0, tzinfo=UTC),
        "full_name": "Sofia Martínez",
    }
    defaults.update(kwargs)
    return defaults


def _make_stats_row(**kwargs):
    defaults = {
        "total_scanned": 10,
        "high_risk": 3,
        "medium_risk": 4,
        "low_risk": 3,
        "avg_score": 420.0,
        "flagged_today": 2,
    }
    defaults.update(kwargs)
    return defaults


def _make_blocked_app_row(**kwargs):
    defaults = {
        "id": "aaaa1111-bbbb-cccc-dddd-eeeeeeeeeeee",
        "rejection_reason": "Alto riesgo de fraude detectado",
        "fraud_score": 850,
        "created_at": datetime(2026, 2, 28, 9, 0, 0, tzinfo=UTC),
    }
    defaults.update(kwargs)
    return defaults


# ── helper function tests ─────────────────────────────────────────────────────

class TestHelpers:
    def test_translate_reasons_known_keys(self):
        result = mod._translate_reasons(json.dumps(["high_loan_amount", "duplicate_applications_found"]))
        assert "Monto de préstamo elevado" in result
        assert "Solicitudes duplicadas detectadas" in result

    def test_translate_reasons_unknown_key_falls_back_to_title(self):
        result = mod._translate_reasons(json.dumps(["some_unknown_reason"]))
        assert result == ["Some Unknown Reason"]

    def test_translate_reasons_invalid_json_returns_empty(self):
        result = mod._translate_reasons("not json {{{")
        assert result == []

    def test_translate_reasons_none_returns_empty(self):
        result = mod._translate_reasons(None)
        assert result == []

    def test_relative_time_minutes(self):
        from datetime import timedelta
        dt = datetime.now(UTC) - timedelta(minutes=15)
        result = mod._relative_time(dt)
        assert "M AGO" in result

    def test_relative_time_hours(self):
        from datetime import timedelta
        dt = datetime.now(UTC) - timedelta(hours=3)
        result = mod._relative_time(dt)
        assert "H AGO" in result

    def test_relative_time_days(self):
        from datetime import timedelta
        dt = datetime.now(UTC) - timedelta(days=2)
        result = mod._relative_time(dt)
        assert "D AGO" in result

    def test_relative_time_none_returns_na(self):
        assert mod._relative_time(None) == "N/A"

    def test_derive_details_high_risk(self):
        result = mod._derive_details(800, "HIGH", 2)
        assert result["ipReputation"] == "SUSPICIOUS"
        assert result["deviceFingerprint"] == "SUSPICIOUS"
        assert result["velocityCheck"] == "FAILED"

    def test_derive_details_low_risk(self):
        result = mod._derive_details(100, "LOW", 0)
        assert result["ipReputation"] == "CLEAN"
        assert result["deviceFingerprint"] == "VERIFIED"
        assert result["velocityCheck"] == "PASSED"

    def test_derive_details_medium_risk_one_dup(self):
        result = mod._derive_details(400, "MEDIUM", 1)
        assert result["deviceFingerprint"] == "KNOWN DEVICE"
        assert result["velocityCheck"] == "WARNING"


# ── handler tests ─────────────────────────────────────────────────────────────

class TestGetFraudData:

    def _call(self, flagged=None, stats=None, blocked_count=None, blocked_apps=None, patterns=None):
        """Helper — patch all DB calls and invoke handler."""
        flagged       = [_make_flagged_row()]    if flagged       is None else flagged
        stats_row     = _make_stats_row()        if stats         is None else stats
        blocked_count = {"blocked": 1}           if blocked_count is None else blocked_count
        blocked_apps  = [_make_blocked_app_row()] if blocked_apps is None else blocked_apps
        patterns      = []                       if patterns      is None else patterns

        def _execute_query(query, params=None):
            q = query.strip().lower()
            if "risk_level in" in q:
                return flagged
            if "limit 500" in q:
                return patterns
            if "limit 5" in q:
                return blocked_apps
            return []

        def _execute_query_single(query, params=None):
            q = query.strip().lower()
            if "count(*) as total_scanned" in q:
                return stats_row
            if "count(*) as blocked" in q:
                return blocked_count
            return None

        with patch.object(mod, "execute_query", side_effect=_execute_query), \
             patch.object(mod, "execute_query_single", side_effect=_execute_query_single):
            return mod.get_fraud_data({}, MagicMock())

    def test_returns_200_with_all_sections(self):
        result = self._call()
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "flaggedApplications" in body
        assert "stats" in body
        assert "patterns" in body
        assert "recentBlocked" in body

    def test_flagged_application_fields(self):
        result = self._call()
        body = json.loads(result["body"])
        app = body["flaggedApplications"][0]
        assert "id" in app
        assert "fraudScore" in app
        assert "riskLevel" in app
        assert "flags" in app
        assert "details" in app
        assert app["name"] == "Sofia Martínez"
        assert app["riskLevel"] == "HIGH"

    def test_flagged_reasons_translated(self):
        result = self._call()
        body = json.loads(result["body"])
        flags = body["flaggedApplications"][0]["flags"]
        assert "Monto de préstamo elevado" in flags
        assert "Solicitudes duplicadas detectadas" in flags

    def test_stats_fields(self):
        result = self._call()
        body = json.loads(result["body"])
        stats = body["stats"]
        assert stats["totalScanned"] == 10
        assert stats["highRisk"] == 3
        assert stats["mediumRisk"] == 4
        assert stats["lowRisk"] == 3
        assert stats["blocked"] == 1
        assert stats["flaggedToday"] == 2

    def test_avg_fraud_score_scaled(self):
        result = self._call()
        body = json.loads(result["body"])
        # avg_score=420 → 420/10 = 42.0
        assert body["stats"]["avgFraudScore"] == 42.0

    def test_recent_blocked_fields(self):
        result = self._call()
        body = json.loads(result["body"])
        blocked = body["recentBlocked"][0]
        assert "id" in blocked
        assert "reason" in blocked
        assert "time" in blocked
        assert "score" in blocked
        assert blocked["reason"] == "Alto riesgo de fraude detectado"

    def test_recent_blocked_null_reason_defaults(self):
        row = _make_blocked_app_row(rejection_reason=None)
        result = self._call(blocked_apps=[row])
        body = json.loads(result["body"])
        assert body["recentBlocked"][0]["reason"] == "Alto riesgo de fraude"

    def test_patterns_aggregated_from_reasons(self):
        rows = [
            {"fraud_reasons": json.dumps(["high_loan_amount"])},
            {"fraud_reasons": json.dumps(["high_loan_amount", "duplicate_applications_found"])},
        ]
        result = self._call(patterns=rows)
        body = json.loads(result["body"])
        labels = [p["pattern"] for p in body["patterns"]]
        assert "Monto de préstamo elevado" in labels
        assert "Solicitudes duplicadas detectadas" in labels

    def test_empty_flagged_returns_empty_list(self):
        # Pass empty list for both flagged AND blocked_apps to keep mock unambiguous
        result = self._call(flagged=[], blocked_apps=[])
        body = json.loads(result["body"])
        assert body["flaggedApplications"] == []

    def test_returns_500_on_db_error(self):
        with patch.object(mod, "execute_query", side_effect=Exception("DB down")):
            result = mod.get_fraud_data({}, MagicMock())
        assert result["statusCode"] == 500
        body = json.loads(result["body"])
        assert "Failed to retrieve fraud data" in body.get("message", body.get("error", ""))

    def test_blocked_count_none_defaults_to_zero(self):
        # Explicitly pass blocked_count={"blocked": 0} to test the zero path
        result = self._call(blocked_count={"blocked": 0})
        body = json.loads(result["body"])
        assert body["stats"]["blocked"] == 0
