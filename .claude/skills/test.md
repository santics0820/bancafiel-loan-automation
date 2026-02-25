# test

Run BancaFiel Lambda unit tests.

## Install dependencies (first time)

```bash
pip install pytest pytest-cov moto[s3,sns,rds] boto3 pg8000
```

## Run all tests

```bash
cd /Users/santiagocairesanchez/KPMG/backend
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

**Coverage target: 80% minimum before any Lambda deploy.**

## Run unit tests only

```bash
python -m pytest tests/unit/ -v
```

## Run tests for a specific Lambda

```bash
python -m pytest tests/unit/test_document_processor.py -v
python -m pytest tests/unit/test_data_extractor.py -v
```

## File naming convention

```
backend/tests/
  unit/
    test_document_processor.py      # Lambda #1
    test_data_extractor.py          # Lambda #2
    test_data_validator.py          # Lambda #3
    test_fraud_detector.py          # Lambda #4
    test_approval_notifier.py       # Lambda #5
    test_erp_updater.py             # Lambda #6
    test_notification_sender.py     # Lambda #7
    test_applications_api.py        # API routes
```

## Mocking patterns

### AWS services (moto)
```python
from moto import mock_aws
import boto3

@mock_aws
def test_something():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="bancafiel-incoming-466901690437-dev")
    # ... test code
```

### Database (patch execute_query)
```python
from unittest.mock import patch, MagicMock

@patch("src.lambdas.document_processor.handler.execute_query")
def test_handler_db(mock_query):
    mock_query.return_value = [{"id": 1, "status": "pending"}]
    # ... test code
```

### Standard env vars fixture
```python
import pytest, os

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "bancafiel")
    monkeypatch.setenv("DB_USER", "bancafiel_admin")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("INCOMING_BUCKET", "bancafiel-incoming-466901690437-test")
    monkeypatch.setenv("PROCESSED_BUCKET", "bancafiel-processed-466901690437-test")
    monkeypatch.setenv("REJECTED_BUCKET", "bancafiel-rejected-466901690437-test")
```

## Mandatory test cases per Lambda handler

Every handler must have tests for:
1. **Success (200)** — happy path with valid input
2. **Missing required field (400)** — omit a required body field
3. **DB error (500, no stack trace)** — mock `execute_query` to raise an exception
4. **AWS service error** — mock the relevant boto3 call to raise ClientError

## Per-Lambda test workflow

1. Use `test-writer` agent to generate the test file
2. Run `/test` to verify all tests pass
3. Run `/review-security` to check the Lambda code
4. Run `/deploy` only after 80%+ coverage confirmed
