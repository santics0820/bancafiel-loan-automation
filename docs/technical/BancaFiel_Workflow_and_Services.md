# BancaFiel — Workflow & AWS Services
**Version:** March 2026 · **Stack:** AWS Serverless · **Region:** us-east-1

---

## 1. How the System Works (End-to-End)

### Entry Point
A client submits a loan application through **www.bancafiel.com**. They upload two documents — their INE (national ID) and a proof of address. These files land in an **S3 bucket**, which automatically triggers the processing pipeline. The client also interacts with the system through a REST API for actions like checking status, registering, and logging in.

### Phase 1 — Document Intelligence (Lambdas 1–3)

**Lambda 1 · `processDocument`** — Triggered the moment a file is uploaded to S3. Downloads the document and sends it to **Claude Sonnet via Amazon Bedrock** to perform AI-powered OCR, extracting all relevant fields. Saves the raw result to the database and asynchronously triggers Lambda 2.

**Lambda 2 · `extractData`** — Receives the Bedrock output, verifies it is complete and correctly structured, organizes fields by document type (name, CURP, address, date of birth), then asynchronously triggers Lambda 3.

**Lambda 3 · `validateData`** — The core validation step. Validates all extracted fields, links the customer to the application using their **CURP** (Mexico's unique national ID), creates or finds the customer record in PostgreSQL, and sends the applicant a confirmation email via `notificationSender`. Only triggers Lambda 4 when the INE is processed (contains CURP), preventing the pipeline from running twice.

### Phase 2 — Fraud Detection (Lambda 4)

**Lambda 4 · `detectFraud`** — Runs a fully custom, rule-based fraud scoring algorithm. It checks: debt-to-income ratio, age from CURP, ID consistency, duplicate applications, and blacklists. Produces a risk level:
- **HIGH** → automatic rejection, goes directly to `erpUpdater`
- **MEDIUM / LOW** → routed to analyst for manual review via Step Functions

### Phase 3 — Approval Workflow (Step Functions + Lambda 5)

**Step Functions · Loan Workflow** — Orchestrates the human-in-the-loop approval decision. Routes the application based on fraud risk level and waits for the analyst's response.

**Lambda 5 · `approvalNotifier`** — Sends an HTML email to the analyst with the application details, fraud score, and Approve / Reject action buttons. The analyst's click calls the REST API (`POST /api/loans/{id}/approve` or `/reject`), which feeds back through API Gateway.

### Phase 4 — Decision & Notification (Lambdas 6–7)

**Lambda 6 · `erpUpdater`** — Updates the application status in PostgreSQL and writes a full audit log entry to `application_history`. Asynchronously invokes Lambda 7.

**Lambda 7 · `notificationSender`** — Final step. Sends the applicant their result via **Amazon SES** using Fernando's dark-theme HTML templates:
- `received` → solicitud recibida confirmation
- `approved` → approval email with loan details
- `rejected` → rejection email

---

## 2. AWS Services Used

| Service | Role in BancaFiel |
|---|---|
| **AWS Lambda** | Runs all 7 pipeline steps + REST API handlers — executes only when triggered, zero idle cost |
| **AWS Step Functions** | Orchestrates the analyst approval flow — routes HIGH/MEDIUM/LOW fraud risk to the correct path |
| **Amazon S3** | Stores uploaded loan documents — triggers the pipeline automatically on every upload |
| **Amazon RDS (PostgreSQL)** | Single source of truth — applications, customers, fraud scores, audit history, login accounts |
| **Amazon Bedrock (Claude Sonnet)** | AI-powered OCR — reads and extracts structured data from ID documents |
| **Amazon API Gateway** | Exposes the REST API to the frontend — handles all HTTP requests from both portals |
| **Amazon CloudFront** | Serves both websites globally with low latency — `www.bancafiel.com` (clients) and `analyst.bancafiel.com` (analysts) |
| **Amazon SES** | Sends all transactional HTML emails — received, approved, and rejected notifications |
| **AWS IAM** | Enforces least-privilege access — each Lambda only has permission to call the exact services it needs |
| **AWS ACM** | Manages the SSL/TLS certificate covering all three domains — enforces HTTPS everywhere |
| **CloudFront OAC** | Locks S3 so files can only be served through CloudFront — raw S3 URLs are blocked |
| **AWS SAM** | Defines and deploys the entire backend from a single YAML file — one command to deploy everything |
| **AWS CloudFormation** | Underlying engine used by SAM — manages all AWS resources as a single versioned, rollback-capable stack |

**Total: 13 AWS services** — the same services trusted by Netflix, Airbnb, Apple, Disney, NASA, and 60% of the Fortune 500.
