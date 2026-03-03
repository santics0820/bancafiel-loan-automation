# BancaFiel Backend - AWS Serverless Architecture

**Backend Developer:** [Your Name]

---

## 📋 Overview

Backend services for BancaFiel loan automation using AWS serverless architecture. Handles document processing, fraud detection, credit scoring, and loan workflow orchestration.

---

## 🏗️ Architecture

### AWS Services
- **AWS Lambda** - Serverless functions (Python 3.11)
- **Amazon RDS** - PostgreSQL database
- **AWS Step Functions** - Loan workflow orchestration
- **Amazon S3** - Document storage
- **Amazon Bedrock (Claude Sonnet 4.5)** - OCR for INE and income documents
- **AWS Fraud Detector** - Fraud risk analysis
- **API Gateway** - REST API endpoints
- **Amazon SES** - Email notifications
- **CloudWatch** - Logging and monitoring

---

## 📂 Folder Structure

```
backend/
├── src/
│   ├── lambdas/                    # Lambda functions
│   │   ├── document-processor/     # Bedrock OCR lambda (Claude Sonnet 4.5)
│   │   ├── fraud-detector/         # Fraud detection lambda
│   │   ├── credit-scorer/          # Credit scoring lambda
│   │   └── notification-sender/    # SES notification lambda
│   ├── step-functions/             # Step Function definitions
│   ├── database/                   # Database schemas & migrations
│   │   ├── migrations/             # SQL migration files
│   │   ├── seeds/                  # Sample data
│   │   └── schema.sql              # Database structure
│   ├── api/                        # API Gateway routes
│   └── utils/                      # Shared utilities
├── tests/                          # All tests
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── test-scenarios/             # Business test scenarios
└── infrastructure/                 # IaC templates
    ├── cloudformation/             # CloudFormation YAML files
    └── terraform/                  # Terraform files (alternative)
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- pip or pipenv
- AWS CLI configured (`aws configure`)
- PostgreSQL (local development)
- AWS SAM CLI (for local Lambda testing)

### Installation

1. **Navigate to backend folder**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp ../.env.example ../.env
   # Edit .env with your AWS credentials
   ```

5. **Setup local database**
   ```bash
   # Create PostgreSQL database
   createdb bancafiel_loans

   # Run migrations
   psql bancafiel_loans < src/database/schema.sql

   # Seed sample data (optional)
   psql bancafiel_loans < src/database/seeds/sample_data.sql
   ```

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/unit/
```

### Run Integration Tests
```bash
pytest tests/integration/
```

### Run All Tests
```bash
pytest tests/
```

### Test Coverage
```bash
pytest --cov=src tests/
```

---

## 🔨 Development

### Local Lambda Testing with SAM

```bash
# Test a specific Lambda function
sam local invoke DocumentProcessorFunction --event tests/events/document-upload.json

# Start local API Gateway
sam local start-api
```

### Database Migrations

```bash
# Create new migration
cd src/database/migrations
# Create new SQL file: YYYYMMDD_description.sql

# Apply migration
psql bancafiel_loans < migrations/20260215_add_fraud_score.sql
```

---

## 📦 Lambda Functions

### 1. Document Processor (`document-processor/`)
**Purpose:** Extract text from uploaded INE and income documents using Claude Sonnet 4.5 on Amazon Bedrock

**Input:**
```json
{
  "documentUrl": "s3://bucket/path/to/document.pdf",
  "documentType": "INE" | "income_proof"
}
```

**Output:**
```json
{
  "extractedData": {
    "fullName": "Juan Pérez",
    "curp": "PEJJ850101HDFRNN09",
    "address": "..."
  }
}
```

### 2. Fraud Detector (`fraud-detector/`)
**Purpose:** Analyze application for fraud risk using AWS Fraud Detector

**Input:**
```json
{
  "applicantData": { ... },
  "documentData": { ... }
}
```

**Output:**
```json
{
  "fraudScore": 0.23,
  "riskLevel": "low" | "medium" | "high"
}
```

### 3. Credit Scorer (`credit-scorer/`)
**Purpose:** Calculate credit score based on income, debt, and history

**Input:**
```json
{
  "monthlyIncome": 15000,
  "requestedAmount": 50000,
  "existingDebt": 20000
}
```

**Output:**
```json
{
  "creditScore": 720,
  "recommendation": "approve" | "review" | "reject"
}
```

### 4. Notification Sender (`notification-sender/`)
**Purpose:** Send email notifications via SES

**Input:**
```json
{
  "recipientEmail": "applicant@email.com",
  "templateType": "approval" | "rejection" | "pending",
  "loanData": { ... }
}
```

---

## 🔄 Step Functions Workflow

### Loan Processing Workflow
```
Start
  ↓
Document Upload to S3
  ↓
Document Processor Lambda (Bedrock - Claude Sonnet 4.5)
  ↓
Fraud Detector Lambda
  ↓
Credit Scorer Lambda
  ↓
Insert to RDS (Pending Approval)
  ↓
Notification Sender (Email to Analyst)
  ↓
[WAIT for Human Approval]
  ↓
Update RDS (Approved/Rejected)
  ↓
Notification Sender (Email to Applicant)
  ↓
End
```

---

## 🗄️ Database Schema

### Tables

**applications**
- id (PK)
- applicant_id
- loan_amount
- status (pending, approved, rejected)
- created_at
- updated_at

**applicants**
- id (PK)
- full_name
- curp
- email
- phone
- created_at

**documents**
- id (PK)
- application_id (FK)
- document_type
- s3_url
- bedrock_extracted_data (JSONB)
- uploaded_at

**fraud_scores**
- id (PK)
- application_id (FK)
- score
- risk_level
- created_at

**credit_scores**
- id (PK)
- application_id (FK)
- score
- recommendation
- created_at

---

## 🚢 Deployment

### Deploy to AWS

```bash
# Using provided deployment script
cd /Users/santiagocairesanchez/KPMG
./scripts/deploy-backend.sh

# Or manually with CloudFormation
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/lambda.yaml \
  --stack-name bancafiel-backend \
  --capabilities CAPABILITY_IAM
```

### Deploy Individual Lambda

```bash
# Zip function
cd src/lambdas/document-processor
zip -r function.zip .

# Upload to AWS
aws lambda update-function-code \
  --function-name DocumentProcessorFunction \
  --zip-file fileb://function.zip
```

---

## 🔐 Security

### IAM Roles Required
- Lambda execution role (access to S3, RDS, Bedrock, Fraud Detector, SES)
- RDS security group (allow Lambda access)
- S3 bucket policies (encrypted at rest)

### Best Practices
- ✅ Use IAM roles, not hardcoded credentials
- ✅ Encrypt environment variables
- ✅ Enable CloudWatch logging
- ✅ Use VPC for RDS access
- ✅ Validate all inputs
- ✅ SQL injection prevention (use parameterized queries)

---

## 📊 Monitoring

### CloudWatch Logs
```bash
# View Lambda logs
aws logs tail /aws/lambda/DocumentProcessorFunction --follow
```

### Metrics to Watch
- Lambda invocation count
- Lambda error rate
- RDS connection count
- API Gateway 4xx/5xx errors
- Step Function execution failures

---

## 🐛 Debugging

### Common Issues

**Lambda timeout**
```
Solution: Increase timeout in CloudFormation template or AWS console
```

**RDS connection refused**
```
Solution: Check Lambda is in same VPC as RDS, security groups allow connection
```

**Bedrock rate limiting**
```
Solution: Implement exponential backoff retry logic
```

---

## 📚 Additional Resources

- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [AWS Step Functions](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)
- [Amazon Bedrock](https://docs.aws.amazon.com/bedrock/)
- [PostgreSQL on RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html)

---

## 👨‍💻 Development Workflow

1. Create feature branch: `git checkout -b feature/backend-your-feature`
2. Develop locally with SAM
3. Write unit tests
4. Run tests: `pytest tests/`
5. Commit and push
6. Create PR to `dev` branch
7. After approval, deploy to AWS

---

**Questions?** Contact the backend developer or check `docs/api-contracts/`
