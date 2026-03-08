# AWS Architecture for BancaFiel Digital Transformation
## Complete Infrastructure Design — As Built (March 2026)

---

## Overview: Manual Process → AWS Automation

| Manual Step | Current Time | AWS Solution | Target Time |
|-------------|--------------|--------------|-------------|
| 1. Receive emails | Hours | Web upload form → S3 → Lambda | Seconds |
| 2. Download attachments | Manual | Automatic S3 storage | Instant |
| 3. Extract/Analyze data | Hours | Claude Sonnet 4.5 on Amazon Bedrock + Lambda | < 1 min |
| 4. Validate against DB | Manual | Lambda + RDS queries | < 1 min |
| 5. Capture in Excel | Manual | RDS automatic | Instant |
| 6. Send to approver | Manual email | SNS/SES + Step Functions | Instant |
| 7. Approval decision | Hours/Days | Web app + Lambda | Minutes |
| 8. Upload to ERP | Manual | Lambda integration | Instant |
| **TOTAL** | **~1 week** | **Automated workflow** | **< 2 hours** |

---

## Solution Approach: Human Approval Required

**Design Decision:**
Human approval is **REQUIRED** for all credit decisions because:

1. ✅ **Unknown Business Rules** - Specific approval criteria gathered from BancaFiel
2. ✅ **Regulatory Compliance** - Banking regulations require human oversight
3. ✅ **Conservative & Safe Approach** - Builds trust with executives
4. ✅ **Still Massive Time Savings** - Even with human approval: 97% time reduction

**What's Automated vs. What's Manual:**

| Step | Automation | Status |
|------|------------|--------|
| Document receipt | ✅ Automated (S3 upload) | Live |
| Document extraction | ✅ Automated (Claude Sonnet 4.5 via Bedrock) | Live |
| Data validation | ✅ Automated (Lambda + RDS) | Live |
| Fraud detection | ✅ Rule-based Lambda scoring | Live |
| Customer creation | ✅ Automated (RDS) | Live |
| Routing to approver | ✅ Automated (Step Functions) | Live |
| **Approval decision** | ❌ **Human required (analyst dashboard)** | Live |
| ERP update | ✅ Automated (Lambda) | Live |
| Customer notification | ✅ Automated (SES) | Live (sandbox) |

---

## 7-Lambda Async Pipeline (As Built)

```
S3 upload (bancafiel-incoming-466901690437-dev)
  └─► [1] processDocument  — downloads doc from S3, runs OCR via Claude Sonnet 4.5 (Bedrock)
        └─► async invoke
              └─► [2] extractData  — verifies Bedrock extraction, triggers validateData
                    └─► async invoke
                          └─► [3] validateData  — validates fields, links customer by CURP
                                └─► async invoke
                                      └─► [4] detectFraud  — rule-based scoring + fraud flags
                                            └─► Step Functions (fraud_risk_level)
                                                  ├─ HIGH  → AutoReject
                                                  ├─ MEDIUM → [5] approvalNotifier (senior)
                                                  └─ LOW   → [5] approvalNotifier (analyst)
                                                                └─► API: POST /api/loans/{id}/approve|reject
                                                                      └─► [6] updateERP  — updates DB + audit log
                                                                            └─► async invoke
                                                                                  └─► [7] notificationSender — SES email
```

**API Lambdas (REST):**
- `listApplications` — GET /api/loans
- `getApplication` — GET /api/loans/{id}
- `getApplicationStatus` — GET /api/loans/status (client tracking)
- `getAnalytics` — GET /api/analytics
- `submitApplication` — POST /api/loans
- `authRegister` — POST /api/auth/register
- `authLogin` — POST /api/auth/login
- `healthCheck` — GET /health

---

## Core AWS Services — As Deployed

### 1. Frontend Hosting

#### **Amazon S3 + CloudFront** ✅ LIVE
- **Bucket:** `bancafiel-frontend-466901690437`
- **CloudFront Distribution:** `E3Q95XT9PA3Z2K` → `d1j3ntjthptj5c.cloudfront.net`
- **Custom Domain:** `www.bancafiel.com` (DNS via GoDaddy → CloudFront)
- **SSL:** AWS ACM certificate (bancafiel.com + www.bancafiel.com) — TLS 1.2+ only
- **HTTPS:** Enforced — HTTP redirects to HTTPS (301), API path is https-only
- **API Proxy:** CloudFront `/api/*` → API Gateway (eliminates CORS, Safari-compatible)
- **Frontend framework:** React + Vite

> **Note:** Amplify was considered but S3 + CloudFront was chosen for full control and to solve Safari cross-origin restrictions via CloudFront path-based routing.

---

### 2. Document Ingestion & Storage

#### **Amazon S3** ✅ LIVE
- `bancafiel-incoming-466901690437-dev` — Raw uploads (INE scans, proof of address)
- `bancafiel-processed-466901690437-dev` — Processed documents
- S3 → Lambda trigger (Events: on the Lambda, not S3 NotificationConfiguration)

---

### 3. Document Processing & Data Extraction

#### **Claude Sonnet 4.5 on Amazon Bedrock** ✅ LIVE
- Model: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Extracts: CURP, full name, DOB, address from INE (front + back combined JPEG)
- Structured JSON output — no custom parsing logic
- Understands Mexican document formats natively (INE, CURP, RFC)
- OCR prompt includes explicit CURP format rules to prevent extraction errors

---

### 4. Compute

#### **AWS Lambda (Python 3.13)** ✅ LIVE
- Stack: `bancafiel-backend-dev` deployed via AWS SAM
- Runtime: Python 3.13, x86_64
- DB driver: `pg8000.native` only (pure Python, no compilation)
- Shared layer: `src/layers/python/utils/` (database, logger, response helpers)
- All handlers: structured JSON response + try/except + logging

---

### 5. Workflow Orchestration

#### **AWS Step Functions** ✅ LIVE
- ARN: `arn:aws:states:us-east-1:466901690437:stateMachine:bancafiel-loan-workflow-dev`
- Routes by `fraud_risk_level`: HIGH → AutoReject, MEDIUM → Senior, LOW → Analyst

---

### 6. Data Storage

#### **Amazon RDS (PostgreSQL 15.7)** ✅ LIVE
- Instance: `db.t3.micro` (free tier)
- Endpoint: `bancafiel-postgres-dev.cyhm06yo4hhg.us-east-1.rds.amazonaws.com`
- SSL required (`ssl_context=True` on all connections)
- Key tables: `customers`, `applications`, `application_history`, `client_accounts`
- `client_accounts` — custom client auth (email, PBKDF2 password hash, session token)

---

### 7. API Layer

#### **Amazon API Gateway (REST)** ✅ LIVE
- URL: `https://nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev`
- CORS: `AllowOrigin: '*'` (dev) — to be locked to `bancafiel.com` for prod
- Auth: `DefaultAuthorizer: NONE` — Cognito planned for future

---

### 8. Authentication

#### **Custom Client Auth** ✅ LIVE (built in-house)
- Table: `client_accounts` in RDS
- Password hashing: PBKDF2-HMAC-SHA256, 200,000 iterations, random salt
- Session tokens: `secrets.token_urlsafe(32)`, stored per user
- Endpoints: `POST /api/auth/register`, `POST /api/auth/login`
- Frontend: 2-step flow for new clients (email → password)

> **Note:** Amazon Cognito was originally planned but not implemented. Custom auth was built to meet the demo timeline. Cognito remains the recommended path for production.

---

### 9. Fraud Detection

#### **Rule-based Lambda (detectFraud)** ✅ LIVE
Fraud is scored in Lambda using business rules:
- High debt-to-income ratio (>60%)
- Loan amount > $100,000 MXN
- CURP/DOB mismatch
- INE expired
- Duplicate applications (same CURP)
- Applicant under 18

Risk level: `HIGH` / `MEDIUM` / `LOW` → drives Step Functions routing

> **Note:** Amazon Fraud Detector (ML-based) was originally planned but not implemented. The rule-based approach is sufficient for demo scale and avoids the $7.50/1,000 predictions cost.

---

### 10. Notifications

#### **Amazon SES** ✅ LIVE (sandbox mode)
- Verified sender: `bancafiel.noreply@gmail.com`
- Region: `us-east-1`
- Status: Sandbox (production access request pending — university project use case submitted)
- Sends: application received, approval, rejection

#### **Amazon SNS** ✅ LIVE
- Topic: `bancafiel-approver-notify-dev`
- Notifies analysts when applications reach approval queue

---

### 11. Monitoring

#### **Amazon CloudWatch** ✅ LIVE
- Lambda logs: `/aws/lambda/bancafiel-*`
- Used for debugging pipeline issues (CURP extraction errors, DB errors, etc.)

---

### 12. Deployment

#### **AWS SAM (Serverless Application Model)** ✅ LIVE
- Template: `backend/template.yaml`
- Config: `backend/samconfig.toml`
- Deploy bucket: `bancafiel-sam-deploy-466901690437`
- Command: `sam build && sam deploy --config-file samconfig.toml --no-confirm-changeset`
- Capabilities: `CAPABILITY_NAMED_IAM`

---


## Architecture Diagram (As Built)

```
┌─────────────────────────────────────────────────────────────┐
│               CLIENT INTERFACE (www.bancafiel.com)           │
│  React + Vite → S3 + CloudFront (E3Q95XT9PA3Z2K)           │
│  - INE camera scan (KYC)                                     │
│  - Loan application submission                               │
│  - Real-time status tracking (folio lookup)                  │
│  - Auth: register / login (client_accounts in RDS)          │
│  - Card reveal + LiquidDashboard (post-approval)            │
└──────────────────────┬──────────────────────────────────────┘
                       │ CloudFront /api/* proxy
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              API GATEWAY (REST) — us-east-1                  │
│  nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev         │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
   ┌─────────┐   ┌──────────┐      ┌──────────┐
   │  Auth   │   │  Loans   │      │Analytics │
   │Register │   │ Submit   │      │ Health   │
   │ Login   │   │ List/Get │      │  Fraud   │
   └────┬────┘   └────┬─────┘      └────┬─────┘
        │              │                 │
        └──────────────▼─────────────────┘
                   RDS PostgreSQL
          (customers, applications, client_accounts,
                  application_history)

DOCUMENT PROCESSING PIPELINE (async):
─────────────────────────────────────
S3 Upload
  └─► Lambda: processDocument
        └─► Claude Sonnet 4.5 (Bedrock OCR — INE, proof of address)
              └─► Lambda: extractData
                    └─► Lambda: validateData → RDS (CURP lookup)
                          └─► Lambda: detectFraud (rule-based scoring)
                                └─► Step Functions
                                      ├─ HIGH → AutoReject → SES
                                      └─ MED/LOW → SNS → Analyst Dashboard
                                                         └─► POST /approve|reject
                                                               └─► Lambda: updateERP → RDS
                                                                     └─► Lambda: notificationSender → SES

ANALYST DASHBOARD:
──────────────────
React (AnalystDashboard.jsx)
  - Applications list with status filters
  - Fraud score, AI analysis, document details
  - Approve / Reject buttons (instant UI update, debounced)
  - Overview + FraudDetection panels
```

---

## Infrastructure Summary

| Resource | Name / ID | Status |
|---|---|---|
| CloudFront | `E3Q95XT9PA3Z2K` | ✅ Deployed |
| Domain | `www.bancafiel.com` | ✅ Live |
| SSL Certificate | ACM `0a063f26-...` | ✅ Issued |
| API Gateway | `nfgxyb0os2` | ✅ Live |
| RDS | `bancafiel-postgres-dev` | ✅ Live |
| S3 Incoming | `bancafiel-incoming-466901690437-dev` | ✅ Live |
| S3 Frontend | `bancafiel-frontend-466901690437` | ✅ Live |
| Step Functions | `bancafiel-loan-workflow-dev` | ✅ Live |
| SES Sender | `bancafiel.noreply@gmail.com` | ✅ Sandbox |
| SAM Stack | `bancafiel-backend-dev` | ✅ Live |
| AWS Account | `466901690437` | us-east-1 |

---

## Git Repository Structure

```
main          ← protected, production-ready
  └─ dev      ← integration branch (all PRs merge here)
       └─ feature/name-what  ← individual work branches
```

Team: Santiago (backend/AWS), Fernando (frontend), Ricardo (fraud/approval tests),
Lizet (notifications/ERP tests), Montse (OCR parsers/tests)
