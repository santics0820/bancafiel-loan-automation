# BancaFiel — Claude Code Standing Orders

## Project Identity
- **App:** BancaFiel — serverless loan processing system (Mexican banking context)
- **Stack:** React + Vite (frontend) · Python 3.13 Lambdas (backend) · PostgreSQL 15.7 on RDS · AWS SAM
- **AWS Account:** 466901690437 | **Region:** us-east-1
- **Stack name:** `bancafiel-backend-dev` | **SAM deploy bucket:** `bancafiel-sam-deploy-466901690437`
- **Deadline:** 4 weeks from project start | **Team:** 5 developers
- **Docs:** `docs/technical/` | **API contracts:** `docs/api-contracts/`

---

## CRITICAL — PATH Fix (prefix ALL sam/aws commands with this)

```bash
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
```

Every terminal session that runs `sam` or `aws` CLI **must** start with this export.
Without it, `sam: command not found` errors occur even when SAM is installed.

---

## 7-Lambda Async Pipeline

```
S3 upload (incoming bucket)
  └─► [1] processDocument  — starts Textract job, saves document metadata to DB
        └─► SNS: bancafiel-textract-done-{env}
              └─► [2] extractData  — gets Textract results, structures fields, saves to DB
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

## CloudFormation / SAM Rules — NEVER VIOLATE

1. **IAM Resource ARNs:** Use `!Sub` string patterns only.
   - CORRECT: `Resource: !Sub "arn:aws:s3:::bancafiel-incoming-${AWS::AccountId}-${Environment}/*"`
   - WRONG: `Resource: !GetAtt IncomingDocumentsBucket.Arn` in IAM → causes circular dependency
2. **S3 → Lambda triggers:** Define in `Events:` on the Lambda, NOT in `NotificationConfiguration:` on the S3 bucket.
   - SAM handles the circular dependency automatically when using `Events: S3:`.
3. **Capabilities:** Always deploy with `CAPABILITY_NAMED_IAM`.
4. **Free-tier RDS settings (already in template):** `BackupRetentionPeriod: 0`, `StorageEncrypted: false`, `PubliclyAccessible: true`.
5. **Stack name:** `bancafiel-backend-dev` (dev) / `bancafiel-backend-prod` (prod)

---

## Code Conventions

- **Every Lambda handler:** wrap in `try/except`; return structured JSON response.
- **Logging:** Use `logger = logging.getLogger(__name__)`. Log event on entry, log errors on except.
- **Response helpers:** Return `{"statusCode": 200, "body": json.dumps(...)}` shape for API Lambdas.
- **Validation:** Use Pydantic for request body validation on all POST/PUT API routes.
- **Error responses:** Never expose stack traces — return generic `{"error": "Internal server error"}` for 500s.
- **Layer imports:** Shared code lives in `src/layers/python/utils/`. Lambdas import as `from utils.database import ...`

---

## Lambda Naming Convention

`bancafiel-{camelCaseName}-{Environment}`

Examples: `bancafiel-processDocument-dev`, `bancafiel-extractData-dev`

---

## Current Technical Debt (as of project start)

- No unit tests yet — coverage target 80% before any Lambda deploy
- No Cognito auth yet — API Gateway has `DefaultAuthorizer: NONE`
- Frontend (`frontend/src/`) uses mock/hardcoded data — real API wiring in Week 3
- DB passwords in `samconfig.toml` — migrate to Secrets Manager before prod
- CORS `AllowOrigin: '*'` — acceptable for dev, lock down for prod
- `DBPassword=BancaFiel2024Secure!` is in samconfig.toml — **never commit samconfig.toml to public repo**

---

## Available Workflows (Skills)

| Command | When to use |
|---|---|
| `/deploy` | Deploy backend to AWS |
| `/db-connect` | Connect to RDS and apply schema |
| `/test` | Run Lambda unit tests |
| `/review-security` | Pre-deploy security checklist — run before every `sam deploy` |

---

## Git Workflow — NEVER VIOLATE

**Branch structure:**
```
main        ← protected, production-ready only
  └─ dev    ← integration branch, all PRs merge here first
       └─ feature/your-name-what-you-built  ← your working branch
```

**Branch naming convention:**
```
feature/santiago-processDocument
feature/fernando-dashboard-ui
feature/teammate1-validateData
fix/santiago-db-connection-error
```

**Rules:**
- NEVER push directly to `main` or `dev`
- Always branch off `dev`, always PR back to `dev`
- Santiago reviews all PRs before merging to `dev`
- Only Santiago merges `dev → main`

**Every time someone asks you to commit or push**, remind them:
1. Are you on a feature branch? (`git branch` to check)
2. Have you run `/test` and `/review-security`?
3. Push to your feature branch, then open a PR to `dev` on GitHub — not to `main`
