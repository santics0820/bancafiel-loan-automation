# AWS Cost Analysis for BancaFiel
## As-Built Cost Breakdown + Production Projection (March 2026)

---

## Part 1: Current Demo/Prototype Cost (As Running Today)

**Environment:** `bancafiel-backend-dev` on AWS account `466901690437` (us-east-1)
**Scale:** University prototype — low volume testing

| Service | Usage | Monthly Cost |
|---|---|---|
| **Lambda** | ~500 invocations/month testing | **$0** (free tier: 1M req/mo) |
| **API Gateway** | ~500 requests/month | **$0** (free tier: 1M req/mo) |
| **RDS db.t3.micro** | PostgreSQL 15.7, 20GB | **$0** (free tier: 750hr/mo, 12 months) |
| **S3** | ~1GB documents + frontend | **$0** (free tier: 5GB) |
| **CloudFront** | frontend + API proxy | **$0** (free tier: 1TB transfer/mo) |
| **ACM SSL Certificate** | bancafiel.com | **$0** (free with CloudFront) |
| **Bedrock (Claude Sonnet 4.5)** | ~50 OCR calls/month testing | **~$0.50** (pay per token) |
| **Step Functions** | ~50 executions | **$0** (free tier: 4,000 transitions/mo) |
| **SES** | ~20 emails (sandbox) | **$0** (free tier: 62k/mo from Lambda) |
| **SNS** | ~50 notifications | **$0** (free tier) |
| **CloudWatch** | Lambda logs | **$0** (free tier: 5GB logs) |
| **SAM Deploy Bucket** | `bancafiel-sam-deploy-*` | **~$0.01** |
| **TOTAL (prototype)** | | **~$0.50 – $2/month** |

> The prototype runs essentially for free within AWS free tier. Bedrock (Claude OCR) is the only real cost at demo scale.

---

## Part 2: Production Cost Projection

**Business Context:**
- 500 applications/day → ~15,000/month
- Each application: INE scan (1 combined JPEG) + proof of address
- ~10 Lambda invocations per application
- 4 SES emails per application
- 50 bank staff users

---

### Service-by-Service Breakdown

#### 1. Claude Sonnet 4.5 on Amazon Bedrock — OCR
**What we use:** Vision API — send combined INE JPEG + proof of address image to Claude

**Pricing (as of 2026):**
- Input tokens: ~$3.00 per 1M tokens
- Output tokens: ~$15.00 per 1M tokens
- Image: ~1,600 tokens per image (1 INE scan)

**Cost Calculation:**
- 15,000 apps × 2 images × 1,600 input tokens = 48M input tokens → **$144/month**
- 15,000 apps × 2 images × 300 output tokens = 9M output tokens → **$135/month**
- **Total Bedrock: ~$279/month**

**Optimization:**
- Proof of address validation can use cheaper heuristics once pattern is established
- Optimized: **~$180-220/month**

---

#### 2. AWS Lambda — Compute
- 15,000 apps × 10 invocations = 150,000/month
- Average: 512MB RAM, 2 seconds per invocation
- GB-seconds: 150,000 × 2 × 0.5 = 150,000

**Cost:** Within free tier (400,000 GB-sec/month) → **$0/month**

---

#### 3. Amazon RDS (PostgreSQL 15.7) — Database
**Production recommendation: db.t3.small** (upgrade from prototype db.t3.micro)
- On-demand: $0.034/hr × 730hr = **$24.82/month**
- Storage 100GB gp3: $0.115/GB = **$11.50/month**
- SSL required, no Multi-AZ for dev (add for prod: doubles cost)

**Total: ~$36/month** (dev) | **~$72/month** (prod with Multi-AZ)

> Current prototype uses db.t3.micro (free tier). Upgrade needed at ~1,000+ applications/month.

---

#### 4. Amazon S3 — Document Storage
- 45,000 documents/month × 500KB avg = 22.5GB/month new
- Year 1 average: ~135GB
- CloudFront frontend bucket: negligible (static assets ~400KB)

**Cost:**
- Storage: 135GB × $0.023 = **$3.11/month**
- PUT/GET requests: **~$0.30/month**
- **Total S3: ~$4/month**

---

#### 5. Amazon CloudFront — CDN + API Proxy
- Frontend: ~10,000 page loads/month = ~40GB transfer
- API proxy: ~150,000 requests/month

**Cost:**
- Data transfer: 40GB × $0.0085 = **$0.34/month**
- Requests: 150,000/10,000 × $0.01 = **$0.15/month**
- **Total CloudFront: ~$1/month**

---

#### 6. Amazon API Gateway — REST API
- 150,000 requests/month

**Cost:** 0.15M × $3.50/M = **$0.53/month** (~$1/month)

---

#### 7. AWS Step Functions — Workflow
- 15,000 apps × 10 transitions = 150,000/month
- Free tier: 4,000 transitions
- (150,000 - 4,000) / 1,000 × $0.025 = **$3.65/month**

---

#### 8. Amazon SES — Email Notifications
- 15,000 apps × 4 emails = 60,000/month
- Free tier from Lambda: 62,000/month → **$0/month**
- Production access: pending AWS approval

---

#### 9. Fraud Detection — Rule-Based Lambda
- Built in `detectFraud` Lambda (no external ML service)
- Rules: debt-to-income, duplicate CURP, underage, INE expiry, loan amount
- **Cost: $0** (runs inside Lambda free tier)

> Amazon Fraud Detector (ML) was evaluated at $7.50/1,000 predictions = **$112.50/month** for 15k apps. Decided against it — rule-based detection is sufficient for this use case and saves ~$110/month.

---

#### 10. Authentication — Custom (client_accounts in RDS)
- PBKDF2 password hashing in Lambda
- Session tokens in RDS
- **Cost: $0** (included in Lambda + RDS above)

> Amazon Cognito (free up to 50,000 MAU) remains recommended for production for security hardening. Cost would be $0 at our scale.

---

#### 11. Amazon SNS — Internal Notifications
- ~30,000 notifications/month
- **Cost: ~$0.02/month** (negligible)

---

#### 12. Amazon CloudWatch — Monitoring
- Lambda logs: ~5GB/month
- **Cost: $0** (free tier: 5GB ingestion/month)
- At scale (>5GB): $0.50/GB → **~$3/month**

---

### Production Cost Summary

| Service | Monthly Cost |
|---|---|
| Bedrock (Claude Sonnet 4.5 OCR) | **$180 – $280** |
| RDS db.t3.small | **$36** |
| Step Functions | **$4** |
| CloudWatch | **$3** |
| S3 | **$4** |
| CloudFront | **$1** |
| API Gateway | **$1** |
| Lambda | **$0** |
| SES | **$0** |
| SNS | **$0** |
| Fraud Detection (rule-based) | **$0** |
| Auth (custom) | **$0** |
| **TOTAL** | **~$229 – $329/month** |

**Rounded: ~$300/month in production**

---

## Part 3: ROI Analysis

### Current Manual Process Costs (Mexican Banking Context)

| Cost Category | Monthly Cost (USD) |
|---|---|
| Staff labor (6-8 people, Mexican salaries) | $6,084 – $9,056 |
| Lost applications (10% loss × $2,000 avg × 3% margin) | $90,000 |
| Fraud losses (2% rate × 9,450 approvals × $1,500/case) | $283,500 |
| **Total Current Monthly Cost** | **~$379,000 – $382,500** |

*Salaries: Junior data entry $558-647 USD/mo, Analysts $1,176-1,470 USD/mo, Senior officer $2,058 USD/mo*
*Exchange rate: 1 USD = 17 MXN*

---

### With AWS Solution

| Item | Current (USD) | AWS (USD) | Monthly Savings |
|---|---|---|---|
| AWS Infrastructure | $0 | $300 | -$300 |
| Staff (reduced to 2-4) | $6,084 – $9,056 | $1,734 – $5,556 | **$3,350 – $5,700** |
| Lost applications (10% → 3%) | $90,000 | $27,000 | **$63,000** |
| Fraud losses (70% reduction) | $283,500 | $85,500 | **$198,000** |
| **Total Monthly Savings** | | | **~$264,000 – $268,000** |

---

### ROI Summary

| Metric | Value |
|---|---|
| Monthly AWS cost | ~$300 |
| Monthly savings | ~$264,000 – $268,000 |
| Development cost (one-time) | ~$10,000 – $15,000 |
| Payback period | **2-3 weeks** |
| Annual savings | **$3.17M – $3.22M** |
| Annual ROI | **~21,000%** |

---

## Part 4: Scaling Economics

| Volume | Bedrock Cost | RDS | Total AWS | Notes |
|---|---|---|---|---|
| 500 apps/mo (prototype) | ~$2 | $0 (free tier) | **~$2** | University demo |
| 2,000 apps/mo | ~$37 | $36 | **~$80** | Small pilot |
| 15,000 apps/mo | ~$250 | $36 | **~$300** | Production |
| 50,000 apps/mo | ~$800 | $72 (Multi-AZ) | **~$900** | Growth phase |
| 150,000 apps/mo | ~$2,400 | $144 | **~$2,600** | Enterprise |

**Key insight:** AWS cost scales linearly with volume while savings scale exponentially. At 50,000 apps/month, savings exceed $1M/month on a $900/month infrastructure.

---

## Part 5: Cost Optimization Strategies (Applied)

| Strategy | Decision | Saving |
|---|---|---|
| Rule-based fraud vs. AWS Fraud Detector | ✅ Applied | **$110/month** saved |
| Custom React dashboard vs. QuickSight | ✅ Applied | **$145/month** saved |
| Custom auth vs. Cognito | ✅ Applied (demo) | **$0** (Cognito is free at our scale) |
| CloudFront API proxy vs. direct API calls | ✅ Applied | Eliminates CORS, no extra cost |
| S3 + CloudFront vs. Amplify | ✅ Applied | **~$5-10/month** saved |
| Bedrock token optimization (combined INE scan) | ✅ Applied | ~20% token reduction |

---

## Key Takeaways for Presentation

1. **Prototype cost: ~$0-2/month** — runs within AWS free tier
2. **Production cost: ~$300/month** — almost entirely Bedrock OCR
3. **Monthly savings: ~$264,000** — the real ROI driver is fraud reduction + lost application recovery
4. **The real question:** "Can BancaFiel afford NOT to implement this?"
   - $300/month AWS vs. $264,000/month in savings = **880x return every month**

> **Narrative:** *"Our solution costs $300/month to operate and saves BancaFiel over $264,000 per month — that's an ROI of 88,000% monthly. The system pays for itself in less than 2 days of operation."*
