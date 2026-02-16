# Architecture Documentation
**Owners:** Backend & Frontend Developers

---

## 📋 Purpose

This folder contains architecture diagrams, design decisions, and technical specifications.

---

## 📂 What Goes Here

- `aws-architecture-diagram.png` - Visual diagram of AWS services
- `database-schema.png` - RDS database ERD (Entity Relationship Diagram)
- `api-architecture.md` - How API Gateway connects to Lambda
- `frontend-architecture.md` - React component hierarchy
- `security-architecture.md` - How we secure data, encryption, IAM roles
- `deployment-architecture.md` - CI/CD pipeline flow

---

## 🎨 Tools for Creating Diagrams

- **Draw.io** (free) - https://app.diagrams.net/
- **Lucidchart** - https://www.lucidchart.com/
- **AWS Architecture Icons** - https://aws.amazon.com/architecture/icons/

---

## 📊 Example: AWS Architecture Diagram

Should show:
```
User (Browser)
    ↓
AWS Amplify (Frontend)
    ↓
API Gateway
    ↓
Lambda Functions (Document Processor, Fraud Detector, Credit Scorer)
    ↓
RDS PostgreSQL + S3 Storage + AWS Textract + Fraud Detector
    ↓
Step Functions (Orchestration)
    ↓
SES (Email Notifications)
```

---

## 🔗 Related Documents

- [`../../03_Technical_Reference/AWS_Architecture_Design.md`](../../03_Technical_Reference/AWS_Architecture_Design.md) - Detailed AWS service descriptions
- [`../api-contracts/`](../api-contracts/) - API specifications

---

**Place all architectural diagrams and design docs here!**
