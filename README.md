# BancaFiel Loan Automation System
**KPMG Consulting Project - AWS Cloud Solution**

---

## 🎯 Project Overview

Automated loan processing system for BancaFiel using AWS services to reduce processing time from 48-72 hours to under 1 hour while maintaining human oversight for all credit decisions.

### Key Metrics
- **Current Cost**: ~$381,000 USD/month
- **Projected AWS Cost**: ~$300 USD/month
- **Monthly Savings**: $264,625 USD
- **Processing Time**: 48-72h → <1h
- **Automation Rate**: 90% automated, 100% human-approved

---

## 👥 Team

| Role | Name | Focus Area |
|------|------|------------|
| **Backend Developer** | [Your Name] | Lambda, RDS, Step Functions, API Gateway |
| **Frontend Developer** | [Friend Name] | React, AWS Amplify, UI/UX |
| **Project Manager** | [PM Name] | Timeline, coordination, standups |
| **Business Analyst** | [BA Name] | ROI analysis, requirements, testing |
| **Change Management** | [CM Name] | Training, stakeholder communications |

---

## 🏗️ Architecture

### AWS Services Used
- **Claude Sonnet 4.5 on Bedrock** - Document OCR (INE, proof of income)
- **AWS Lambda** - Serverless compute (Python 3.11)
- **Amazon RDS** - PostgreSQL database
- **AWS Step Functions** - Workflow orchestration
- **Amazon S3** - Document storage
- **AWS Fraud Detector** - Fraud analysis
- **API Gateway** - REST APIs
- **Amazon Cognito** - Authentication
- **Amazon SES** - Email notifications
- **AWS Amplify** - Frontend hosting
- **CloudWatch** - Monitoring & logging

---

## 📂 Repository Structure

```
bancafiel-loan-automation/
├── backend/           # Backend services (Lambda, RDS, APIs)
├── frontend/          # React frontend application
├── docs/              # All team documentation
├── shared/            # Shared code between frontend/backend
├── scripts/           # Deployment and automation scripts
├── 01_Team_Documents/ # Team briefings and presentations
├── 02_Knowledge_Base/ # Project knowledge and business context
├── 03_Technical_Reference/ # Detailed technical documentation
├── 04_Archive/        # Historical versions
└── 05_Scripts/        # Utility scripts
```

### Quick Links
- 📘 **Backend Setup**: See [`backend/README.md`](./backend/README.md)
- 🎨 **Frontend Setup**: See [`frontend/README.md`](./frontend/README.md)
- 📚 **Documentation**: See [`docs/`](./docs/)
- 🔧 **Scripts**: See [`scripts/`](./scripts/)

---

## 🚀 Quick Start

### Prerequisites
- **AWS Account** with appropriate permissions
- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **PostgreSQL** (local development)
- **Git** installed

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/bancafiel-loan-automation.git
   cd bancafiel-loan-automation
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials and configuration
   ```

3. **Backend Setup**
   ```bash
   cd backend
   # See backend/README.md for detailed instructions
   ```

4. **Frontend Setup**
   ```bash
   cd frontend
   # See frontend/README.md for detailed instructions
   ```

---

## 🔄 Git Workflow

### Branch Strategy
```
main       # Production-ready code
└── dev    # Development integration branch
    ├── feature/backend-*
    ├── feature/frontend-*
    └── docs/*
```

### Creating a Feature Branch
```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

### Committing Changes
```bash
git add .
git commit -m "Brief description of changes"
git push origin feature/your-feature-name
```

### Creating a Pull Request
1. Push your feature branch
2. Create PR on GitHub: `feature/your-branch` → `dev`
3. Request review from team lead
4. Merge after approval

---

## 📋 Project Management

### Daily Standup (10 min)
- **When**: 9:00 AM daily
- **Format**: What I did yesterday, what I'm doing today, blockers
- **PM tracks** progress in `docs/project-management/`

### Weekly Demo (30 min)
- **When**: Friday 3:00 PM
- **Format**: Show working features, discuss next week

---

## 📖 Documentation

### For All Team Members
- [`docs/architecture/`](./docs/architecture/) - System architecture diagrams
- [`docs/api-contracts/`](./docs/api-contracts/) - API specifications
- [`docs/meeting-notes/`](./docs/meeting-notes/) - Team meeting notes

### For Business Analyst
- [`docs/business/`](./docs/business/) - ROI analysis, requirements

### For Project Manager
- [`docs/project-management/`](./docs/project-management/) - Timeline, progress tracking

### For Change Management
- [`docs/change-management/`](./docs/change-management/) - Training plans, stakeholder communications

### Team Documents
- [`01_Team_Documents/`](./01_Team_Documents/) - Team briefings and presentations
- [`02_Knowledge_Base/`](./02_Knowledge_Base/) - Project knowledge base
- [`03_Technical_Reference/`](./03_Technical_Reference/) - Technical documentation

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Test Scenarios
- Business Analyst maintains test scenarios in:
  - `backend/tests/test-scenarios/`
  - `frontend/tests/test-scenarios/`

---

## 🚢 Deployment

### Backend Deployment
```bash
./scripts/deploy-backend.sh
```

### Frontend Deployment
```bash
./scripts/deploy-frontend.sh
```

---

## 📊 Project Timeline

**Duration**: 4 weeks

- **Week 1**: Requirements gathering, architecture setup, repo initialization
- **Week 2**: Backend development (Lambda, RDS, APIs), Frontend foundation
- **Week 3**: Integration, testing, change management documentation
- **Week 4**: Final testing, presentation preparation, deployment

---

## 📞 Support

- **Technical Issues**: Contact backend/frontend developers
- **Business Questions**: Contact Business Analyst
- **Timeline/Coordination**: Contact Project Manager
- **Stakeholder Questions**: Contact Change Management lead

---

## 📄 License

This project is developed for KPMG consulting engagement with BancaFiel.

---

**Last Updated:** February 15, 2026
**Built with ❤️ by KPMG Consulting Team**
