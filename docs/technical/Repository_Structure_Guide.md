# BancaFiel Repository Structure Guide
**Team Reference - How to Organize Our Code**

---

## Repository Structure (Monorepo)

```
bancafiel-loan-automation/
│
├── README.md                          # Project overview, setup instructions
├── .gitignore                         # Ignore node_modules, .env, etc.
├── .env.example                       # Example environment variables
│
├── docs/                              # 📚 Documentation (ALL TEAM)
│   ├── architecture/                  # AWS architecture diagrams
│   ├── business/                      # BA: ROI analysis, requirements
│   ├── change-management/             # Change mgmt: training docs
│   ├── project-management/            # PM: timeline, standups, progress
│   ├── meeting-notes/                 # All team meeting notes
│   └── api-contracts/                 # Frontend/backend API agreements
│
├── backend/                           # 🔧 Backend (You)
│   ├── README.md                      # Backend setup instructions
│   ├── src/
│   │   ├── lambdas/                   # AWS Lambda functions
│   │   │   ├── document-processor/    # Textract OCR lambda
│   │   │   ├── fraud-detector/        # Fraud Detector lambda
│   │   │   ├── credit-scorer/         # Credit scoring lambda
│   │   │   └── notification-sender/   # SES notification lambda
│   │   ├── step-functions/            # Step Functions workflows
│   │   │   └── loan-workflow.json     # Main orchestration
│   │   ├── database/                  # RDS PostgreSQL
│   │   │   ├── migrations/            # Database schema changes
│   │   │   ├── seeds/                 # Sample data
│   │   │   └── schema.sql             # Database structure
│   │   ├── api/                       # API Gateway routes
│   │   │   └── routes/                # REST API endpoints
│   │   └── utils/                     # Shared utilities
│   │
│   ├── tests/                         # Backend tests
│   │   ├── unit/                      # Unit tests
│   │   ├── integration/               # Integration tests
│   │   └── test-scenarios/            # 📝 BA can contribute here!
│   │       └── test-cases.md          # Business test scenarios
│   │
│   └── infrastructure/                # AWS infrastructure
│       ├── cloudformation/            # CloudFormation templates
│       │   ├── lambda.yaml
│       │   ├── rds.yaml
│       │   └── step-functions.yaml
│       └── terraform/                 # (Alternative to CloudFormation)
│
├── frontend/                          # 🎨 Frontend (Your friend)
│   ├── README.md                      # Frontend setup instructions
│   ├── public/                        # Static assets
│   ├── src/
│   │   ├── components/                # React components
│   │   │   ├── Dashboard/
│   │   │   ├── LoanApplication/
│   │   │   ├── ApprovalQueue/
│   │   │   └── Analytics/
│   │   ├── pages/                     # Main pages
│   │   ├── services/                  # API calls to backend
│   │   ├── utils/                     # Utilities
│   │   └── App.js                     # Main app
│   │
│   ├── tests/                         # Frontend tests
│   │   └── test-scenarios/            # 📝 BA can contribute here!
│   │
│   ├── package.json                   # Dependencies
│   └── amplify.yml                    # AWS Amplify config
│
├── shared/                            # 🔗 Shared code
│   ├── types/                         # TypeScript types (if using TS)
│   ├── constants/                     # Shared constants
│   └── validation/                    # Shared validation logic
│
├── scripts/                           # 🛠️ Automation scripts
│   ├── setup.sh                       # Initial setup
│   ├── deploy-backend.sh              # Deploy backend to AWS
│   ├── deploy-frontend.sh             # Deploy frontend to Amplify
│   └── seed-database.sh               # Populate test data
│
├── .github/                           # GitHub workflows
│   └── workflows/
│       ├── backend-ci.yml             # Backend CI/CD
│       └── frontend-ci.yml            # Frontend CI/CD
│
└── package.json                       # Root package.json (monorepo tools)
```

---

## How Each Team Member Uses the Repo

### You (Backend Developer)
- Work in `backend/` folder
- Create Lambda functions, API routes, database schemas
- Deploy using `scripts/deploy-backend.sh`
- Update `docs/api-contracts/` when APIs change

### Frontend Developer
- Work in `frontend/` folder
- Build React components, integrate APIs
- Deploy using `scripts/deploy-frontend.sh`
- Check `docs/api-contracts/` for API specs

### Business Analyst
- Add ROI analysis to `docs/business/roi-analysis.md`
- Write test scenarios in `backend/tests/test-scenarios/test-cases.md`
- Document requirements in `docs/business/requirements.md`
- Review and approve `docs/api-contracts/` for business logic

### Project Manager
- Update timeline in `docs/project-management/timeline.md`
- Track progress in `docs/project-management/sprint-progress.md`
- Document meeting notes in `docs/meeting-notes/`
- Manage GitHub Issues and Project Board

### Change Management
- Create training materials in `docs/change-management/training-plan.md`
- Document user guides in `docs/change-management/user-guide.md`
- Write stakeholder communication in `docs/change-management/communications/`

---

## Git Workflow for Your Team

### Branch Strategy (Keep it Simple!)

```
main                    # Production-ready code
├── dev                 # Development branch (integrate here first)
    ├── feature/backend-ocr-lambda
    ├── feature/frontend-dashboard
    ├── docs/roi-analysis
    └── docs/training-plan
```

### Workflow Steps

1. **Create Feature Branch**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes & Commit**
   ```bash
   git add .
   git commit -m "Add OCR lambda function"
   ```

3. **Push & Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request on GitHub: feature → dev
   ```

4. **Review & Merge**
   - PM or tech lead reviews
   - Merge to `dev`
   - Weekly: merge `dev` → `main`

---

## Daily Standup Integration

**Each person reports using the repo:**
- "Yesterday: Worked on `backend/lambdas/document-processor/`"
- "Today: Adding tests to `backend/tests/integration/`"
- "Blocker: Need API contract finalized in `docs/api-contracts/`"

---

## Key Files to Create First

### 1. `README.md` (Root)
```markdown
# BancaFiel Loan Automation System

## Quick Start
- Backend: See `backend/README.md`
- Frontend: See `frontend/README.md`

## Team
- Backend: [Your name]
- Frontend: [Friend name]
- PM: [PM name]
- BA: [BA name]
- Change Mgmt: [CM name]

## Documentation
See `docs/` folder
```

### 2. `.gitignore`
```
# Dependencies
node_modules/
venv/

# Environment
.env
.env.local

# AWS
.aws-sam/

# IDE
.vscode/
.idea/

# OS
.DS_Store

# Build
dist/
build/

# Personal (like your personal_info folder!)
personal_info/
```

### 3. `docs/api-contracts/loan-api.md`
```markdown
# Loan API Contract

## POST /api/loans
Request:
{
  "applicantId": "string",
  "loanAmount": number,
  "documents": ["s3-urls"]
}

Response:
{
  "loanId": "string",
  "status": "pending|approved|rejected"
}
```

---

## Technology Stack

### Backend
- **Language**: Python 3.11 (Lambda runtime)
- **Database**: PostgreSQL on RDS
- **API**: API Gateway + Lambda
- **Storage**: S3
- **Orchestration**: Step Functions

### Frontend
- **Framework**: React 18
- **Hosting**: AWS Amplify
- **API Calls**: Axios
- **UI Library**: Material-UI or Tailwind CSS

### Infrastructure
- **IaC**: CloudFormation or Terraform
- **CI/CD**: GitHub Actions

---

## Repository Setup Commands

```bash
# 1. Create repo on GitHub
# Name: bancafiel-loan-automation

# 2. Clone locally
git clone https://github.com/your-org/bancafiel-loan-automation.git
cd bancafiel-loan-automation

# 3. Create folder structure
mkdir -p docs/{architecture,business,change-management,project-management,meeting-notes,api-contracts}
mkdir -p backend/{src/{lambdas,step-functions,database,api,utils},tests/{unit,integration,test-scenarios},infrastructure/{cloudformation,terraform}}
mkdir -p frontend/{public,src/{components,pages,services,utils},tests}
mkdir -p shared/{types,constants,validation}
mkdir -p scripts
mkdir -p .github/workflows

# 4. Create README files
touch README.md
touch backend/README.md
touch frontend/README.md

# 5. Create .gitignore
touch .gitignore

# 6. Initial commit
git add .
git commit -m "Initial project structure"
git push origin main

# 7. Create dev branch
git checkout -b dev
git push origin dev
```

---

## Why This Structure Works

✅ **Clear Separation**: Backend/Frontend clearly separated but in one place
✅ **Non-Technical Inclusion**: `docs/` folder makes everyone feel included
✅ **Easy Collaboration**: Frontend dev can see backend changes immediately
✅ **Single Deployment**: One repo = one deployment pipeline
✅ **Project Management**: PM can track everything in one GitHub Projects board
✅ **Business Analysis**: BA can contribute test scenarios and requirements
✅ **Change Management**: CM can version training materials with code

---

## GitHub Projects Board Setup

Create columns:
1. **Backlog** - All tasks
2. **In Progress** - Currently working
3. **Review** - PRs awaiting review
4. **Testing** - BA testing
5. **Done** - Completed

Each task has labels:
- `backend` - Backend work
- `frontend` - Frontend work
- `docs` - Documentation
- `bug` - Bug fixes
- `enhancement` - New features

---

## When to Create a Second Repo

**Only if:**
- Team grows beyond 10 people
- Backend and frontend deploy on completely different schedules
- Different teams own backend vs frontend

**For your case:** Stick with monorepo! 🎯
