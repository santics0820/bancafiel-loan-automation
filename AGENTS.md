# BancaFiel — Codex Standing Orders

## Project Identity
- **App:** BancaFiel — serverless loan processing system (Mexican banking context)
- **Stack:** React + Vite (frontend) · Python 3.13 Lambdas (backend) · PostgreSQL 15.7 on RDS · AWS SAM
- **AWS Account:** 466901690437 | **Region:** us-east-1
- **Deadline:** 4 weeks from project start | **Team:** 5 developers
- **Docs:** `docs/technical/` | **API contracts:** `docs/api-contracts/`

---

## 7-Lambda Async Pipeline

```
S3 upload (incoming bucket)
  └─► [1] processDocument  — starts Bedrock OCR (Claude Sonnet 4.5) job, saves document metadata to DB
        └─► async invoke → Bedrock extraction complete
              └─► [2] extractData  — verifies Bedrock extraction, triggers validateData
                    └─► async invoke
                          └─► [3] validateData  — validates fields, links customer by CURP
                                └─► async invoke
                                      └─► [4] detectFraud  — AWS Fraud Detector, scores risk
                                            └─► Step Functions (fraud_risk_level)
                                                  ├─ HIGH  → AutoReject
                                                  ├─ MEDIUM → [5] approvalNotifier (senior)
                                                  └─ LOW   → [5] approvalNotifier (analyst)
                                                                └─► API: POST /api/loans/{id}/approve|reject
                                                                      └─► [6] updateERP  — updates DB + audit log
                                                                            └─► async invoke
                                                                                  └─► [7] notificationSender — SES email
```

**API Lambdas (REST):** listApplications · getApplication · getAnalytics · submitApplication · healthCheck

---

## Database Rules — NEVER VIOLATE

1. **Driver:** `pg8000.native` only. Never use psycopg2, asyncpg, or any other driver.
2. **Connection:** Always pass `ssl_context=True` — RDS requires SSL.
3. **Placeholders:** Write SQL with `%s` markers; call `_convert_placeholders()` before `conn.run()`.
   - `_convert_placeholders` rewrites `%s` → `$1, $2, …` for pg8000 positional params.
4. **Params:** Pass as a flat list/tuple. Use `_pg_params()` helper to normalise.
5. **No hardcoded credentials.** All DB config comes from `os.environ` only.
6. **Pattern:**
   ```python
   from utils.database import execute_query, execute_insert
   rows = execute_query("SELECT * FROM applications WHERE id = %s", (app_id,))
   ```

---

## Code Conventions

- **Every Lambda handler:** wrap in `try/except`; return structured JSON response.
- **Logging:** Use `logger = logging.getLogger(__name__)`. Log event on entry, log errors on except.
- **Response helpers:** Return `{"statusCode": 200, "body": json.dumps(...)}` shape for API Lambdas.
- **Error responses:** Never expose stack traces — return generic `{"error": "Internal server error"}` for 500s.
- **Layer imports:** Shared code lives in `src/layers/python/utils/`. Lambdas import as `from utils.database import ...`

---

## Lambda Naming Convention

`bancafiel-{camelCaseName}-{Environment}`

Examples: `bancafiel-processDocument-dev`, `bancafiel-extractData-dev`

---

## Test Infrastructure (how Ricardo's tests are structured — follow this pattern)

- Tests live in `backend/tests/unit/`
- Run from the `backend/` directory: `python -m pytest tests/ -v`
- `backend/tests/conftest.py` injects mock `utils.database`, `utils.logger`, `utils.response` via `sys.modules` — no real DB or AWS calls needed
- Handlers are loaded via `importlib.util` with `boto3.client` patched at load time
- All patches use `patch.object(mod, ...)` on the loaded module
- **Coverage target: 80% minimum** — check with `python -m pytest tests/ --cov=src/lambdas/{name} --cov-report=term-missing`
- Reference examples: `backend/tests/unit/test_fraud_detector.py`, `backend/tests/unit/test_approval_notifier.py`

---

## Test Coverage Progress

| Lambda | Owner | Tests | Coverage | Status |
|---|---|---|---|---|
| `detectFraud` | Ricardo | `tests/unit/test_fraud_detector.py` | 83% | ✅ Done — merged to dev |
| `approvalNotifier` | Ricardo | `tests/unit/test_approval_notifier.py` | 83% | ✅ Done — merged to dev |
| `notificationSender` | Lizet | — | 0% | 🔲 Pending |
| `erpUpdater` | Lizet | — | 0% | 🔲 Pending |
| `processDocument` | Montse | — | 0% | 🔲 Pending |
| `validateData` | Montse | — | 0% | 🔲 Pending |
| `extractData` | Montse | — | 0% | 🔲 Pending (OCR parsers also pending) |

**Other open items:**
- Health endpoint bug — `execute_query_single` not imported in `health.py` (Lizet)
- Analytics tests (Lizet)
- `extract_bank_statement_fields()` and `extract_income_fields()` TODOs in `data-extractor` (Montse)

---

## Team Roles & Ownership

| Person | GitHub | Role | Owns |
|---|---|---|---|
| **Santiago** | `santics0820` | Backend lead + AWS admin | Architecture, infrastructure, PR reviews, deploys |
| **Fernando** | `nitrofgm` | Frontend lead | React app (`frontend/`), UI components, API wiring in Week 3 |
| **Ricardo** | `ricfranco05` | Backend contributor | Fraud & Approval pipeline — `detectFraud`, `approvalNotifier`, their tests, Step Functions verification |
| **Lizet** | `lizetpinae-ux` | Backend contributor | Customer communications — `notificationSender`, `erpUpdater`, their tests, health endpoint fix, analytics tests |
| **Montse** | `Mon500` | Backend contributor | Document intelligence — `extractData` OCR parsers (bank statement + income), `processDocument` + `validateData` tests |

**When someone tells you their name, look them up here and tailor your help to their specific ownership area.**

### What each person needs installed
- **Ricardo, Lizet, Montse:** VS Code, Git, Python 3.13 only — no AWS CLI, no SAM, no credentials needed
- **First command:** `pip install pytest pytest-cov moto[s3,sns] boto3 pg8000`

---

## Git Workflow — NEVER VIOLATE

**Branch structure:**
```
main        ← protected, production-ready only
  └─ dev    ← integration branch, all PRs merge here first
       └─ feature/your-name-what-you-built  ← your working branch
```

**Rules:**
- NEVER push directly to `main` or `dev`
- Always branch off `dev`, always PR back to `dev`
- Santiago reviews all PRs before merging to `dev`
- Only Santiago merges `dev → main`

**Every time someone asks you to commit or push**, remind them:
1. Are you on a feature branch? (`git branch` to check)
2. Have you run `python -m pytest tests/ -v`?
3. Push to your feature branch, then open a PR to `dev` on GitHub — not to `main`

### Branch naming for each person
```
feature/lizet-notification-tests
feature/lizet-health-fix
feature/montse-ocr-parsers
feature/montse-extractor-tests
```

---

## Key File Paths

- DB utilities: `backend/src/layers/python/utils/database.py`
- Schema: `backend/src/database/schema.sql`
- Lambdas: `backend/src/lambdas/{name}/handler.py`
- Tests: `backend/tests/unit/`
- Test config: `backend/tests/conftest.py`, `backend/pytest.ini`
