"""
conftest.py — shared test setup for BancaFiel backend tests

Injects lightweight fakes into sys.modules for:
  - utils.database  → MagicMock (all DB calls need per-test patching)
  - utils.logger    → real logging stubs (no side-effects)
  - utils.response  → real implementations (so statusCode checks work)

This runs BEFORE any handler module is imported, so the `from utils.xxx import`
statements inside each Lambda handler resolve to these fakes instead of
trying to connect to a real DB or requiring pg8000.
"""
import sys
import json
import logging
import types
from unittest.mock import MagicMock


# ── utils.logger — real stubs so log calls are silent no-ops ─────────────────
_logger_module = types.SimpleNamespace(
    setup_logger=lambda name: logging.getLogger(name),
    log_event=lambda logger, event_type, data: None,
    log_error=lambda logger, error_type, error, context=None: None,
)

# ── utils.database — MagicMock; each test configures return values itself ─────
_database_module = MagicMock()

# ── utils.response — real implementations so result['statusCode'] works ───────
def _success_response(data, status_code=200):
    return {"statusCode": status_code, "body": json.dumps(data, default=str)}

def _error_response(message, status_code=400, error_code=None):
    return {"statusCode": status_code, "body": json.dumps({"error": True, "message": message})}

def _not_found_response(message="Not found"):
    return {"statusCode": 404, "body": json.dumps({"error": True, "message": message})}

_response_module = types.SimpleNamespace(
    success_response=_success_response,
    error_response=_error_response,
    not_found_response=_not_found_response,
)

# ── Inject into sys.modules before any handler is loaded ──────────────────────
sys.modules.setdefault("utils", MagicMock())
sys.modules["utils.database"] = _database_module
sys.modules["utils.logger"] = _logger_module
sys.modules["utils.response"] = _response_module
