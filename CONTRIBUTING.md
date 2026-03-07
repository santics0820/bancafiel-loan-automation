# Welcome to BancaFiel

This document gets you from zero to contributing in one read. No prior experience with AWS, Claude, or professional Git workflows required.

---

## Section 1 — The Problem We're Solving

BancaFiel is a bank that processes around 500 loan and credit card applications every day. The problem is that today this process is entirely manual and takes about **one week** from the moment a customer submits their documents to the moment they get an answer.

Here's what that looks like in practice today:

1. A customer emails their documents (ID, proof of address, income proof) to a shared Outlook inbox
2. A bank employee downloads the attachments manually
3. A team leader opens each PDF and reads it to extract the relevant data — name, CURP, income, etc.
4. Another person cross-checks that data against the bank's internal database
5. Someone types everything into an Excel spreadsheet
6. The file gets forwarded by email to the right approver
7. The approver reads it, decides, and replies
8. An admin manually records the decision in the bank's internal system
9. An admin sends the customer an email with the result

Because every step depends on a person being available, 10% of applications get lost in the process. Fraud is rising because humans make mistakes when reviewing hundreds of documents. Customers are leaving for banks that respond in hours.

**Our job is to automate all 9 of those steps using AWS cloud services, so the whole process runs in under 2 hours, automatically, without anyone needing to open an email.**

---

## Section 2 — The Architecture

Before the table, here's a plain-English glossary of the services we use:

| Term | What it is in plain English |
|---|---|
| **Lambda** | A Python function that runs on AWS. It turns on when triggered, does its job, and turns off. You pay only for the seconds it runs. |
| **S3** | AWS file storage — like Google Drive for our system. Documents land here. |
| **API Gateway** | The front door of our backend. Receives requests from the web app and routes them to the right Lambda. |
| **RDS PostgreSQL** | Our database. Stores all customer records, applications, and decisions. |
| **Bedrock OCR (Claude Sonnet 4.5)** | An AWS service that reads PDFs and images and extracts text — like a very fast, accurate human reader. |
| **SNS** | A messaging system. When one service finishes, it sends a notification to trigger the next one. |
| **Step Functions** | A workflow manager. Routes the application to the right approver based on fraud risk level. |
| **Fraud Detector** | An AWS ML service that scores how risky an application looks based on patterns. |
| **SES** | AWS email service. Sends professional emails to customers automatically. |

### How the 9 manual steps become 7 automated Lambdas

| # | Manual Step (Today) | AWS Service | Our Lambda |
|---|---|---|---|
| 1 | Customer emails documents; team downloads attachments manually | API Gateway + S3 | `submitApplication` — web form uploads documents directly to S3 |
| 2 | Team leader opens each PDF and reads it by hand | Claude Sonnet 4.5 on Amazon Bedrock | `processDocument` — triggered by S3 upload, sends PDF to Bedrock OCR (Claude Sonnet 4.5) |
| 3 | Team leader waits, then structures the extracted data | SNS + Bedrock OCR (Claude Sonnet 4.5) async | `extractData` — triggered when Bedrock OCR (Claude Sonnet 4.5) finishes; saves structured fields to DB |
| 4 | Cross-checks document data against the bank's system | RDS PostgreSQL | `validateData` — queries DB by CURP automatically, flags mismatches |
| 5 | Admin types everything into Excel | RDS PostgreSQL | Already done — data is in the DB after step 4 |
| 6 | File forwarded by email to the right approver | Fraud Detector + Step Functions | `detectFraud` — scores risk; Step Functions routes LOW → analyst, MEDIUM → senior, HIGH → auto-reject |
| 7 | Approver downloads file, decides | SNS + API Gateway | `approvalNotifier` — notifies approver with a link; they click approve/reject in the dashboard |
| 8 | Admin records decision in internal ERP | RDS PostgreSQL | `updateERP` — writes decision and audit trail to DB instantly |
| 9 | Admin sends outcome email to customer | Amazon SES | `notificationSender` — sends email to customer within seconds of decision |

---

## Section 3 — Tool Setup

Install these tools in order. Each one has a written guide and a video tutorial.

---

### 1. VS Code (code editor)

This is where you write and read code. Think of it as Microsoft Word, but for programming.

**Install:** [https://code.visualstudio.com](https://code.visualstudio.com)

> **Watch first — Official 7-minute beginner tutorial by Microsoft:**
> [Learn Visual Studio Code in 7 Minutes (Official)](https://learn.microsoft.com/en-us/shows/visual-studio-code/learn-visual-studio-code-in-7min-official-beginner-tutorial)
>
> Covers: opening folders, navigating the interface, creating files, installing extensions, and changing themes. Everything you need before writing your first line.

After installing, open VS Code and install these two extensions (click the blocks icon on the left sidebar, search by name):
- **Python** (by Microsoft)
- **GitLens** (makes Git history visible inside VS Code)

---

### 2. Git + GitHub account

Git is how we track changes to code and collaborate without overwriting each other's work. GitHub is where the repository lives online.

**Install Git:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
**Create a GitHub account:** [https://github.com](https://github.com)

> **Watch first — Complete Git & GitHub Tutorial for Beginners (2024):**
> [https://www.youtube.com/watch?v=MuZySo5lF8E](https://www.youtube.com/watch?v=MuZySo5lF8E)
>
> This covers everything you'll actually use day-to-day: installation, committing, branching, pushing, and pull requests. Highly recommended before touching the repo.

After installing, run these two commands in your terminal to identify yourself to Git:
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

Then ask Santiago to add you as a collaborator on the GitHub repository.

---

### 3. Python 3.13

Required to run and understand the Lambda functions.

**Install:** [https://www.python.org/downloads](https://www.python.org/downloads)

Verify it installed correctly:
```bash
python --version   # should show 3.13.x
```

---

### 4. Node.js

Required to run the React web app locally.

**Install the LTS version:** [https://nodejs.org/en/download](https://nodejs.org/en/download)

Verify:
```bash
node --version   # should print a version number
```

---

### 5. AWS SAM CLI

This is the tool that packages and deploys the Lambda functions to AWS. You only need this if you're working on the backend infrastructure.

**Install guide:** [https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

Verify:
```bash
sam --version   # should show SAM CLI version
```

---

### 6. Claude Code CLI

This is the AI assistant that already knows our entire project. You run it inside VS Code's terminal and talk to it like a colleague. It reads our project's `CLAUDE.md` file at the start of every session, so it already understands the architecture, the rules, and the codebase.

**Install guide:** [https://docs.anthropic.com/en/docs/claude-code/getting-started](https://docs.anthropic.com/en/docs/claude-code/getting-started)

> **Watch first — Claude Code Beginner's Tutorial by Peter Yang (15 min, 2025):**
> [https://www.youtube.com/watch?v=GepHGs_CZdk](https://www.youtube.com/watch?v=GepHGs_CZdk)
>
> Shows exactly how to start Claude Code, how `CLAUDE.md` works, how to use plan mode before writing code, and how to build a real feature from scratch. Watch this before your first session.

To start it, open the terminal inside VS Code and run:
```bash
claude
```

---

## Section 4 — How This Repo Works

### Folder structure

```
KPMG/
├── frontend/          React web app — the interface customers and analysts use
├── backend/           Python Lambdas, database schema, SAM infrastructure
│   ├── src/
│   │   ├── lambdas/   One folder per Lambda function
│   │   ├── api/       REST API route handlers
│   │   ├── layers/    Shared utilities (database connection, logging)
│   │   └── database/  SQL schema
│   ├── template.yaml  Defines all AWS resources (the "blueprint" of the cloud)
│   └── samconfig.toml Deploy configuration — NEVER commit this publicly
├── docs/              Architecture diagrams, API contracts, business case
└── .claude/
    ├── CLAUDE.md      Claude's standing orders for this project
    └── skills/        Shortcut commands you can run inside Claude
```

### What CLAUDE.md is

`CLAUDE.md` is a file that Claude reads automatically at the start of every session. It tells Claude everything about the project — the architecture, the rules, the naming conventions, the database driver we use, the AWS patterns that work.

**Never delete or rename it.** Without it, every session would need to re-explain the entire project from scratch.

### Skills — shortcuts you run inside Claude

When you're in a Claude session, you can type a `/command` to run a pre-defined workflow:

| Command | What it does |
|---|---|
| `/deploy` | Runs the full SAM build + deploy sequence with the correct AWS configuration |
| `/test` | Runs all unit tests with coverage report |
| `/db-connect` | Connects to the database and walks you through applying the schema |
| `/review-security` | Runs a security checklist before deploying |

### Talking to Claude

Claude already knows the project. You can say things like:

- *"Explain the validateData Lambda to me"*
- *"Write tests for the extractData handler"*
- *"I'm getting a circular dependency error in CloudFormation, what do I do?"*
- *"What does the `_convert_placeholders` function do?"*

You don't need to explain the architecture every time — Claude reads `CLAUDE.md` at the start of every session.

---

## Section 5 — Git Workflow

**The rule:** No one pushes directly to `main` or `dev`. All work happens on a feature branch, which gets reviewed before merging.

```
main        ← protected, production-ready only
  └─ dev    ← integration branch, all PRs merge here first
       └─ feature/your-name-what-you-built  ← your working branch
```

### Every time you start new work

```bash
# 1. Make sure you have the latest version of dev
git checkout dev
git pull origin dev

# 2. Create your own branch
# Format: feature/your-name-what-youre-building
git checkout -b feature/yourname-task-name

# Example:
git checkout -b feature/carlos-validateData
```

### While you work — saving your progress

```bash
# See what files you've changed
git status

# Stage the specific files you want to save
git add backend/src/lambdas/data-validator/handler.py

# Save them with a message describing what you did
git commit -m "Add validateData handler with CURP lookup"

# Push your branch to GitHub
git push origin feature/carlos-validateData
```

### When you're done — opening a Pull Request

1. Go to the repository on GitHub
2. You'll see a yellow banner: *"Compare & pull request"* — click it
3. Set the base branch to **`dev`** (not `main`)
4. Write a short description of what you built
5. Submit the PR and tag Santiago for review

**You never merge your own PR.** Santiago reviews everything before it touches `dev` or `main`.

> **New to Git branches?** Re-watch the Git tutorial from Section 3 — the second half covers branches and pull requests exactly as we use them here.
> [https://www.youtube.com/watch?v=MuZySo5lF8E](https://www.youtube.com/watch?v=MuZySo5lF8E)

---

## Section 6 — Your First Task

When you're assigned a task, follow this sequence every time:

**1. Understand what you're building**

Open Claude (`claude` in the terminal) and ask:
```
Explain the [task/Lambda name] to me. What does it receive, what does it do, and what does it return?
```

**2. Create your branch**

```bash
git checkout dev
git pull origin dev
git checkout -b feature/yourname-taskname
```

**3. Build with Claude's help**

Open the relevant file in VS Code. Talk to Claude:
```
I'm implementing the validateData Lambda. Read the handler file and help me write the CURP lookup and mismatch detection logic.
```

Claude will read the file, understand the context, and guide you step by step.

**4. Run tests**

In the Claude session, type:
```
/test
```

Fix anything that fails. Aim for 80%+ test coverage before moving on.

**5. Security check**

```
/review-security
```

Fix any issues before pushing.

**6. Push and open a PR**

```bash
git push origin feature/yourname-taskname
```

Go to GitHub, open a PR to `dev`, and tag Santiago for review.

> **First time using Claude Code?** Watch the 15-minute tutorial before your first session — it shows the exact process described above:
> [https://www.youtube.com/watch?v=GepHGs_CZdk](https://www.youtube.com/watch?v=GepHGs_CZdk)

---

## Questions?

Ask Santiago directly, or open a Claude session and describe what you're stuck on. Claude knows the project and can help debug, explain, or guide you through any part of the codebase.
