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
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/santiagocairesanchez/Library/Python/3.13/bin:$PATH"
```

Every terminal session that runs `sam` or `aws` CLI **must** start with this export.
SAM is installed at `/Users/santiagocairesanchez/Library/Python/3.13/bin/sam` via pip.

---

## 7-Lambda Async Pipeline

```
S3 upload (incoming bucket)
  └─► [1] processDocument  — downloads doc from S3, runs OCR via Claude Sonnet 4.5 (Bedrock), saves to DB
        └─► async invoke (Bedrock extraction complete)
              └─► [2] extractData  — verifies Bedrock extraction, triggers validateData
                    └─► async invoke
                          └─► [3] validateData  — validates fields, links customer by CURP
                                └─► async invoke
                                      └─► [4] detectFraud  — rule-based scoring (9 rules: debt ratio, loan amount, duplicates, age, CURP/DOB, INE expiry, address match, proof of address age, recent rejection)
                                            └─► Step Functions (fraud_risk_level)
                                                  ├─ HIGH  → AutoReject
                                                  ├─ MEDIUM → [5] approvalNotifier (senior)
                                                  └─ LOW   → [5] approvalNotifier (analyst)
                                                                └─► API: POST /api/loans/{id}/approve|reject
                                                                      └─► [6] updateERP  — updates DB + audit log
                                                                            └─► async invoke
                                                                                  └─► [7] notificationSender — SES email
```

**API Lambdas (REST):** listApplications · getApplication · getApplicationStatus · getAnalytics · submitApplication · authRegister · authLogin · healthCheck

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

## Deployed Infrastructure

- **Frontend:** `www.bancafiel.com` — React + Vite → S3 + CloudFront (`E3Q95XT9PA3Z2K`)
- **API:** `https://nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev`
- **DB:** `bancafiel-postgres-dev.cyhm06yo4hhg.us-east-1.rds.amazonaws.com`
- **S3 Incoming:** `bancafiel-incoming-466901690437-dev`
- **Vite proxy:** In dev, `API_URL = ''` — all `/api/*` calls go through Vite proxy to API Gateway (fixes Safari cross-origin block on localhost)
- **Auth:** Custom `client_accounts` table in RDS — PBKDF2 hashing, session tokens. Cognito will NOT be implemented.
- **Fraud detection:** Rule-based Lambda (`detectFraud`) — AWS Fraud Detector not implemented (decided against it)
- **SES:** Sandbox — `bancafiel.noreply@gmail.com` verified. Production access request pending.
- **HTTPS:** Enforced via CloudFront — HTTP → HTTPS (301), API path is https-only

## Current Technical Debt

- API Gateway has `DefaultAuthorizer: NONE` — analyst dashboard has no server-side auth (UI separation only, no Cognito)
- DB passwords in `samconfig.toml` — migrate to Secrets Manager before prod
- CORS `AllowOrigin: '*'` — lock down to `bancafiel.com` before prod
- `DBPassword=BancaFiel2024Secure!` is in samconfig.toml — **never commit samconfig.toml to public repo**
- Unit tests still missing for `processDocument`, `validateData`, `extractData` (Montse)

## Test Coverage Progress

| Lambda | Owner | Tests | Coverage | Status |
|---|---|---|---|---|
| `detectFraud` | Ricardo | `tests/unit/test_fraud_detector.py` | 83% | ✅ Done — merged to dev |
| `approvalNotifier` | Ricardo | `tests/unit/test_approval_notifier.py` | 83% | ✅ Done — merged to dev |
| `notificationSender` | Lizet | `tests/unit/test_notification_sender.py` | ✅ | ✅ Done — merged to dev |
| `erpUpdater` | Lizet | `tests/unit/test_erp_updater.py` | ✅ | ✅ Done — merged to dev |
| `processDocument` | Montse | — | 0% | 🔲 Pending |
| `validateData` | Montse | — | 0% | 🔲 Pending |
| `extractData` | Montse | — | 0% | 🔲 Pending (OCR parsers also pending) |

**Other open items:**
- ~~Health endpoint bug~~ — fixed by Lizet ✅
- ~~Analytics tests~~ — done by Lizet ✅
- ~~AWS Fraud Detector~~ — decided not to implement; rule-based Lambda used instead ✅
- ~~SES sender~~ — `bancafiel.noreply@gmail.com` verified in us-east-1 ✅ (sandbox)
- ~~Frontend API wiring~~ — Fernando ✅ merged to dev
- ~~Card reveal animation + approved dashboard~~ — Fernando ✅ merged to dev
- ~~Client auth system~~ — register/login wired end-to-end ✅
- ~~Domain deploy~~ — `www.bancafiel.com` live on CloudFront ✅
- SES production access — pending AWS approval (university project use case submitted)

---

## Available Workflows (Skills)

| Command | When to use |
|---|---|
| `/deploy` | Deploy backend to AWS |
| `/db-connect` | Connect to RDS and apply schema |
| `/test` | Run Lambda unit tests |
| `/review-security` | Pre-deploy security checklist — run before every `sam deploy` |

---

## Team Roles & Ownership

| Person | GitHub | Role | Owns |
|---|---|---|---|
| **Santiago** | `santics0820` | Backend lead + AWS admin | Architecture, infrastructure, PR reviews, deploys |
| **Fernando** | `nitrofgm` | Frontend lead | React app (`frontend/`), UI components, API wiring — see `docs/technical/FRONTEND_WIRING.md` |
| **Ricardo** | `ricfranco05` | Backend contributor | Fraud & Approval pipeline — `detectFraud`, `approvalNotifier`, their tests, Step Functions verification |
| **Lizet** | `lizetpinae-ux` | Backend contributor | Customer communications — `notificationSender`, `erpUpdater`, their tests, health endpoint fix, analytics tests |
| **Montse** | `Mon500` | Backend contributor | Document intelligence — `extractData` OCR parsers (bank statement + income), `processDocument` + `validateData` tests |

**When someone tells you their name, look them up here and tailor your help to their specific ownership area.**

### What each person needs installed
- **Santiago & Fernando:** Everything (Python, Node, SAM CLI, AWS CLI)
- **Ricardo, Lizet, Montse:** VS Code, Git, Claude Code, Python 3.13 only — no AWS CLI, no SAM, no credentials needed
- **First command for Ricardo/Lizet/Montse:** `pip install pytest pytest-cov moto[s3,sns] boto3 pg8000`

### Branch naming for each person
```
feature/ricardo-fraud-tests
feature/ricardo-approval-tests
feature/lizet-notification-tests
feature/lizet-health-fix
feature/montse-ocr-parsers
feature/montse-extractor-tests
feature/fernando-api-wiring
```

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
