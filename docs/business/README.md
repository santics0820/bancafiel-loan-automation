# Business Analysis Documentation
**Owner:** Business Analyst

---

## 📋 Purpose

This folder contains all business analysis deliverables including ROI calculations, requirements documentation, and test scenarios.

---

## 📂 What Goes Here

### ROI Analysis
- `roi-analysis.md` - Cost-benefit analysis
- `current-vs-proposed-costs.xlsx` - Detailed cost breakdown
- `savings-projections.md` - Monthly/annual savings estimates

### Requirements
- `functional-requirements.md` - What the system must do
- `non-functional-requirements.md` - Performance, security, usability
- `business-rules.md` - Mexican banking regulations, loan rules

### User Stories
- `user-stories.md` - Analyst user stories, applicant stories
- `acceptance-criteria.md` - How we know features are complete

### Test Scenarios
- `test-scenarios.md` - Business test cases (link to backend/frontend test folders)

---

## 📊 Key Deliverables

### 1. ROI Analysis (Priority: HIGH)
**File:** `roi-analysis.md`

**What to include:**
- Current monthly costs (staff salaries, lost applications, fraud)
- Proposed AWS costs (~$300/month)
- Monthly savings calculation
- Payback period
- 1-year, 3-year projections

**Why it matters:** KPMG cares most about ROI. This is your most important contribution!

---

### 2. Requirements Documentation
**File:** `functional-requirements.md`

**What to include:**
- User requirements (what analysts need)
- System requirements (what AWS must do)
- Regulatory requirements (Mexican banking laws)

---

### 3. Test Scenarios
**Files:**
- `backend/tests/test-scenarios/test-cases.md`
- `frontend/tests/test-scenarios/test-cases.md`

**What to include:**
Example test scenarios:
```
Test Case 1: Valid Loan Application
- Applicant has income of 15,000 MXN/month
- Requests loan of 50,000 MXN
- Uploads valid INE and income proof
- Expected: Fraud score < 0.3, credit score > 650, approval recommended

Test Case 2: High Fraud Risk
- Applicant provides mismatched CURP on documents
- Expected: Fraud score > 0.7, flagged for review

Test Case 3: Insufficient Income
- Applicant earns 8,000 MXN/month
- Requests 100,000 MXN loan
- Expected: Credit score low, rejection recommended
```

---

## 🎯 How to Contribute

1. **Week 1:** Create ROI analysis from existing cost data
2. **Week 2:** Document functional requirements from Session 2 with KPMG
3. **Week 3:** Write test scenarios for developers to verify
4. **Week 4:** Verify final ROI numbers for presentation

---

## 🔗 Related Documents

- [`../02_Knowledge_Base/AWS_Cost_Analysis.md`](../../02_Knowledge_Base/AWS_Cost_Analysis.md) - Mexican cost context
- [`../02_Knowledge_Base/KPMG_Project_Knowledge_Base.md`](../../02_Knowledge_Base/KPMG_Project_Knowledge_Base.md) - Session 2 questions

---

## 💡 Tips

- **Use Mexican context:** Salaries in MXN, realistic loan amounts
- **Quantify everything:** KPMG wants numbers, not just "faster" or "better"
- **Think like a consultant:** What would impress the client?

---

**Your role is CRITICAL. The best code means nothing without a solid business case!** 🎯
