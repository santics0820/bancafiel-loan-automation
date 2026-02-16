# KPMG Digital Lighthouse - Business Case Project
## Consultancy Project for ITESM Class 2026

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Client Information](#client-information)
3. [Current Situation & Problem](#current-situation--problem)
4. [Detailed Process Breakdown](#detailed-process-breakdown)
5. [The Challenge](#the-challenge)
6. [Required Deliverables](#required-deliverables)
7. [Interview Notes & Additional Information](#interview-notes--additional-information)

---

## Project Overview

**Project Name:** Digital Lighthouse
**Client:** KPMG Cárdenas Dosal, S.C.
**Business Partner:** BancaFiel (fictional case study bank)
**Project Focus:** Process optimization and digital transformation for loan and credit card application processing

---

## Client Information

### BancaFiel - The Bank
- **Background:** A bank established for decades that has been a pillar in the community
- **Current Challenge:** Significant gap in application processing speed compared to competition
- **Daily Volume:** Processes approximately 500 applications per day
- **Geographic Focus:** Operating in one city

### Current vs. Competitive Performance

#### Current Process (BancaFiel):
- **Approval Time:** 1 week to process and approve loan and credit card applications
- **Lost Applications:** 10% of applications are lost before being approved due to complexity and slowness
- **Processing Method:** Manual process with multiple handoffs

#### Competitive Process (Other Banks):
- **Approval Time:** Processing applications in a matter of hours
- **Operational Efficiency:** Minimized losses to as little as 3%
- **Technology:** More modern systems enabling steady flow of approvals

---

## Current Situation & Problem

### Business Impact on BancaFiel

1. **Unhappy Customers**
   - Slow approvals have led to customer dissatisfaction
   - Customers expect a faster and more efficient experience

2. **Loss of Customers**
   - Some customers have moved their accounts to competing banks
   - Seeking more agile services elsewhere

3. **Distrust**
   - Delay in approval has generated distrust in new potential customers
   - Affecting acquisition of new customers

4. **Fraud**
   - Current manual process has led to many man-made mistakes
   - Caused a rise in fraud cases

### The Core Problem

The current procedure consists of:
- Receipt and approval of documents for a specific area of the bank
- Documents in various formats are received by email
- Relevant data is extracted and verified between submitted documents and the bank's database
- Documents are then submitted for approval
- If approved, details are recorded in an internal platform (ERP)

**Process Duration:** Approximately 1 week to complete, including approvals

---

## Detailed Process Breakdown

### Step 1: Receive Documents via Email
- Customer sends the request to a shared Outlook account
- Managed by the bank's Customer Registration area
- Documents include: Proof of Address, INE/IFE, etc.

### Step 2: Download Attachments
- Team in charge of downloading PDF attachments
- Attachments contain customer data

### Step 3: Analyze/Extract Information
- Team leader analyzes information within the attachments
- Classifies each document according to format and information it contains

### Step 4: File Data Validation
- Team leader validates the information
- Compares data to verify if it matches the system
- Determines whether it is a new customer or existing customer previously registered

### Step 5: Capture Information
- Person in charge manually records information in a temporary database (Excel)
- Information is organized and classified

### Step 6: Send Request
- Once information has been classified and captured
- Manually sent to the appropriate approver to continue with the process

### Step 7: Request Approval
- Corresponding approver downloads the file for analysis
- Approves or rejects based on the information it contains

### Step 8: Upload Information
- If approved: Manually registered in internal platform (ERP)
- If rejected: Email sent to customer indicating it was not approved

**Note:** In all cases, the customer must be notified at each stage of the process.

---

## The Challenge

### What BancaFiel is Looking For:

1. **Advanced Technology Implementation**
   - Implementation of new application processing system
   - Leverage modern technologies to streamline workflow

2. **Reduction of Approval Time**
   - Reduce approval time from 1 week to just a few hours
   - Align with competitor standards

3. **Minimize Losses**
   - New platform designed to significantly reduce the 10% loss of requests
   - Improve overall efficiency

4. **Visualization of Metrics**
   - Visibility of potential, current, and past requests
   - Better control of the operation

### Key Questions to Address:

- **How can we help this bank to reduce times and avoid fraud?**
- **How would you quantify the benefits of your solution?**

### Strategic Considerations:

- **Project Management Strategy** - Required
- **Change Management Strategy** - Required

**Goal:** By modernizing its process, the bank hopes to regain the trust of its customers, attract new business, and compete more effectively in the dynamic financial market. Investing in technology upgrading is seen as an essential step to ensure the bank's sustainability and long-term growth in this digital age.

---

## Required Deliverables

### 1. Quantitative Analysis
- Demonstrate how much the bank will improve its operation with the implementation of the solution
- Show measurable improvements and ROI

### 2. High-Level Architecture Proposal

**Components Required:**

a) **High-Level Architecture Diagram**
   - Visual representation of the proposed solution
   - Component mapping

b) **Architecture and Solution Description**
   - Design high-level architecture proposal for the solution
   - For each part of the process, propose how it could be improved/automated
   - Propose alternative solutions mentioning advantages and disadvantages
   - Use as many components as possible for a complete and efficient solution

c) **Component Mapping**
   - Mapping of all components used for the solution

**Note:** Do not limit the resolution of the proposal to a PPT only.

### 3. Project Management Strategy

Required elements:
- Project Objectives
- Project Scope
- Work Plan
- Risk Management
- Control and Monitoring
- Project Closure

### 4. Change Management Strategy

Required elements:
- Change Vision and Objectives
- Stakeholder Analysis
- Communication Strategy
- Training Strategy

---

## Interview Notes & Additional Information

### Session 1 - Initial Presentation
**Date:** [To be filled]
**Contact Person:** [To be filled]
**Topics Covered:**
- Introduction to KPMG
- What consultancy looks like
- Day-to-day basis for a consultant
- Challenge introduction
- Team assignments
- Problem presentation

**Key Takeaways:**
- Limited detail provided in initial session
- Further engagement needed in future private sessions
- Need to better assess the issue through follow-up questions

---

### Future Sessions & Updates

#### Session 2 - Critical Requirements Gathering (30-minute session)
**Date:** [To be filled]
**Duration:** 30 minutes (limited time)
**Objective:** Gather critical information needed to design the solution architecture

---

### **PRIORITY QUESTIONS - Must Answer in Session 2:**

**These 7 questions are CRITICAL for solution design. Focus on these first.**

---

#### **Question 1: Approval Criteria (CRITICAL - 5 min)** ⭐⭐⭐
**Ask:** *"What specific criteria do your approvers use to approve or reject loan and credit card applications?"*

**Why critical:** We cannot design the decision logic or approver dashboard without knowing this.

**Follow-up probes:**
- Are there minimum income requirements?
- Credit score thresholds?
- Debt-to-income ratio limits?
- Employment stability requirements (e.g., 6 months minimum)?
- Are there different rules for loans vs. credit cards?
- Are there different rules based on amount requested?

**What we need to learn:**
- [ ] Specific numeric thresholds (income, credit score, etc.)
- [ ] Knockout criteria (automatic rejection reasons)
- [ ] Different rules by product type or amount
- [ ] Who has authority to approve different amounts

---

#### **Question 2: The "10% Loss" Problem (CRITICAL - 3 min)** ⭐⭐⭐
**Ask:** *"You mentioned 10% of applications are lost before approval. Can you explain exactly what 'lost' means?"*

**Why critical:** We need to understand the root cause to design the right solution.

**Follow-up probes:**
- Are these applications abandoned by customers (they give up waiting)?
- Are they literally lost in the system (emails deleted, paperwork misplaced)?
- At which step in the process do most get lost?
- Can you track where/why they disappear?

**What we need to learn:**
- [ ] Root cause of the 10% loss (customer abandonment vs. system failure)
- [ ] Which process step has the highest loss rate
- [ ] Can we prevent this with better tracking/notifications?

---

#### **Question 3: Current ERP System (CRITICAL - 3 min)** ⭐⭐⭐
**Ask:** *"What ERP or internal system do you currently use to record approved applications?"*

**Why critical:** Our solution must integrate with their existing system.

**Follow-up probes:**
- What platform/software is it? (SAP, Oracle, Microsoft Dynamics, custom-built?)
- Does it have an API we can integrate with?
- Who manages the ERP system? (IT department contact?)
- Do you need real-time updates or can it be batch updates?

**What we need to learn:**
- [ ] Exact ERP system name and version
- [ ] Integration capabilities (API, database access, file import)
- [ ] IT contact for technical integration questions
- [ ] Update frequency requirements (real-time vs. batch)

---

#### **Question 4: Fraud Types & Impact (CRITICAL - 4 min)** ⭐⭐⭐
**Ask:** *"You mentioned fraud cases increased due to manual errors. What types of fraud are you encountering, and what's the financial impact?"*

**Why critical:** Need to quantify the fraud problem and design appropriate detection.

**Follow-up probes:**
- What types of fraud? (Forged documents, identity theft, duplicate apps?)
- How many fraudulent applications per month?
- Average financial loss per fraud case?
- How do you currently detect fraud? (Too late, or catch some?)
- What percentage of approved applications turn out to be fraudulent?

**What we need to learn:**
- [ ] Specific fraud types (so we can design detection rules)
- [ ] Fraud rate (% of applications)
- [ ] Financial impact per month (for ROI calculation)
- [ ] Current fraud detection methods (manual inspection, etc.)

---

#### **Question 5: Regulatory Requirements (CRITICAL - 3 min)** ⭐⭐
**Ask:** *"Are there banking regulations that require a human to approve all credit decisions?"*

**Why critical:** Need to confirm that human approval is required for regulatory compliance.

**Follow-up probes:**
- Mexican banking regulations you must comply with?
- Internal audit requirements?
- Do regulators require human oversight on all lending decisions?
- Are there different rules for small amounts (e.g., credit cards under $5k)?

**What we need to learn:**
- [ ] Regulatory constraints on automation
- [ ] Whether human approval is legally required
- [ ] Different rules for different product types/amounts
- [ ] Audit trail requirements

---

#### **Question 6: Success Metrics (CRITICAL - 3 min)** ⭐⭐
**Ask:** *"How will you measure the success of this project? What specific metrics or KPIs are most important to BancaFiel?"*

**Why critical:** Need to know how they'll evaluate our solution.

**Follow-up probes:**
- Is it primarily about speed (reducing 1 week to X hours)?
- Reducing fraud (by what %)?
- Reducing lost applications (from 10% to X%)?
- Customer satisfaction scores?
- Staff efficiency (fewer people needed)?
- What would make this project a "home run" success?

**What we need to learn:**
- [ ] Primary success metric (time, fraud, loss rate, cost?)
- [ ] Target numbers (e.g., "reduce to under 24 hours")
- [ ] How they currently measure performance
- [ ] Who will evaluate success (executives, board, regulators?)

---

#### **Question 7: Current Volume & Patterns (IMPORTANT - 2 min)** ⭐
**Ask:** *"You mentioned 500 applications per day. Is this consistent year-round, or are there seasonal peaks?"*

**Why critical:** Need to design for peak load, not average.

**Follow-up probes:**
- Are there busy seasons (end of year, holidays)?
- Peak daily volume?
- Breakdown by type (loans vs. credit cards)?
- Growth expectations (will it be 500/day next year or 1000/day)?

**What we need to learn:**
- [ ] Peak volume (for system capacity planning)
- [ ] Product mix (% loans vs. credit cards)
- [ ] Growth projections
- [ ] Seasonal patterns

---

### **If Time Permits (5-7 minutes remaining):**

#### **Bonus Question 8: Approval Authority** ⭐
*"Who has authority to approve different types/amounts of applications? Are there approval limits by role?"*

#### **Bonus Question 9: Timeline Expectations**
*"When would you ideally want this solution operational? Are there any critical deadlines?"*

#### **Bonus Question 10: Existing Customer Data**
*"What customer data do you already have in your system that we could use for validation?"*

---

### **Session 2 Agenda (30-minute structure):**

**0-2 min:** Introduction & recap
- "Thank you for meeting with us. Last session you presented the challenge. Today we need to understand some critical details to design the right solution."

**2-25 min:** CRITICAL QUESTIONS (7 questions, ~3-4 min each)
- Question 1: Approval criteria (5 min)
- Question 2: 10% loss explanation (3 min)
- Question 3: ERP system (3 min)
- Question 4: Fraud types & impact (4 min)
- Question 5: Regulatory requirements (3 min)
- Question 6: Success metrics (3 min)
- Question 7: Volume patterns (2 min)

**25-28 min:** Bonus questions if time allows

**28-30 min:** Wrap-up & next steps
- "Thank you. This gives us what we need to design a solution. We'll return with our proposal showing architecture, cost analysis, and implementation plan."

---

### **Conversation Tips:**

1. **Don't pitch your solution yet** - Just gather information
2. **Take detailed notes** - Assign one person as note-taker
3. **Ask follow-ups** - If they say "yes, we have approval criteria," ask "What are they specifically?"
4. **Get numbers** - Don't accept vague answers, get specific metrics
5. **Prioritize ruthlessly** - If running out of time, skip bonus questions
6. **Record if possible** - Ask "May we record this for our notes?"

---

### **After Session 2 - Immediate Actions:**

Within 24 hours, update this knowledge base with:
- [ ] All answers to the 7 critical questions
- [ ] Any new questions that arose
- [ ] Decisions you can now make (e.g., "Human approval IS required per regulations")
- [ ] What you still don't know and need to find out

---

**Notes:** [To be filled after session]

#### Session 3
**Date:** [To be filled]
**Notes:** [To be added]

---

## Questions for Next Session

*These questions focus on understanding BancaFiel's current process, pain points, and requirements in detail. We ask these BEFORE presenting our solution to ensure we fully understand their needs.*

### **A. Understanding Current Process & Pain Points**

1. **Can you walk us through a typical application from start to finish?**
   - What happens when an application arrives?
   - Who touches it at each stage?
   - Where do most delays occur?

2. **What are the biggest bottlenecks in the current process?**
   - Which step takes the longest?
   - Where do applications get "stuck"?
   - What causes the 10% application loss rate?

3. **What types of errors or problems occur most frequently?**
   - Data entry errors?
   - Document classification mistakes?
   - Communication issues between teams?

4. **How do you currently track application status?**
   - Can customers check their application status?
   - How do staff know where each application is in the process?

### **B. Approval Criteria & Business Rules**

5. **What criteria do approvers use to approve or reject applications?**
   - Income requirements?
   - Credit score thresholds?
   - Debt-to-income ratios?
   - Employment stability requirements?

6. **Are there different approval rules for different products?**
   - Loans vs. credit cards?
   - Different rules based on amount requested?
   - New customers vs. existing customers?

7. **What documentation is absolutely mandatory for approval?**
   - Which documents can never be missing?
   - Are there acceptable substitutes for any documents?

8. **Who has authority to approve what?**
   - Are there approval limits by role?
   - Do larger amounts require senior approval?
   - Is there a committee for high-value applications?

### **C. Fraud & Risk Management**

9. **What types of fraud have you encountered?**
   - Forged documents?
   - Identity theft?
   - Duplicate applications?
   - Other patterns?

10. **How do you currently detect fraud?**
    - Manual inspection of documents?
    - Cross-checking databases?
    - Gut feeling / experience?

11. **What percentage of applications are fraudulent?**
    - How many do you catch?
    - How many slip through?
    - What's the financial impact?

12. **What is your risk tolerance?**
    - Would you prefer to reject some good applications to catch all fraud?
    - Or accept some fraud risk to approve more quickly?

### **D. Systems & Integration**

13. **What is your current ERP system?**
    - What platform/software?
    - Does it have an API for integration?
    - Who manages it?

14. **What other systems would our solution need to integrate with?**
    - Customer database?
    - Credit bureau systems?
    - Email system?
    - Accounting systems?

15. **Do you use any credit bureau services?**
    - Círculo de Crédito, Buró de Crédito?
    - How often do you check credit scores?
    - Is this automated or manual?

### **E. Volume & Metrics**

16. **Can you provide more details on application volume?**
    - 500/day - is this consistent or seasonal?
    - Peak times during month/year?
    - Growth expectations?

17. **What is your current approval rate?**
    - What % get approved vs. rejected?
    - What are the main rejection reasons?

18. **What does the 10% loss rate mean exactly?**
    - Applications abandoned by customers?
    - Applications lost in the system?
    - Where in the process do they get lost?

### **F. Stakeholder Expectations**

19. **What would success look like for this project?**
    - Specific time reduction targets?
    - Error reduction targets?
    - Customer satisfaction improvements?

20. **Who are the key stakeholders?**
    - Who will use the new system daily?
    - Who needs to approve the implementation?
    - Who are the decision-makers?

21. **What are the biggest concerns about changing the process?**
    - Staff resistance to change?
    - Technology concerns?
    - Cost concerns?
    - Regulatory compliance?

### **G. Regulatory & Compliance**

22. **Are there banking regulations we need to consider?**
    - Must a human always approve credit decisions?
    - Data privacy requirements (Mexican banking law)?
    - Audit trail requirements?

23. **How long must you retain application records?**
    - Document retention policies?
    - Audit requirements?

### **H. Customer Communication**

24. **How do you currently notify customers about their application status?**
    - Email, phone, SMS?
    - At what stages do you communicate?
    - What information do you provide?

25. **What do customers complain about most?**
    - Wait time?
    - Lack of updates?
    - Having to provide documents multiple times?

### **I. Success Metrics**

26. **How do you currently measure performance?**
    - Applications processed per day/week?
    - Average processing time?
    - Error rates?
    - Customer satisfaction scores?

27. **What KPIs would you want to see in a new system?**
    - Real-time dashboards?
    - Daily/weekly reports?
    - Alert systems?

### **J. Timeline & Budget**

28. **What is your expected timeline for implementation?**
    - When do you need this operational?
    - Are there any critical deadlines?

29. **What is your budget range for this solution?**
    - One-time implementation cost?
    - Ongoing monthly operational cost?

30. **Do you have IT staff to support this, or would you need managed services?**

---

### **Priority Questions for Next Session:**
*Focus on these first if time is limited:*

1. ✅ **Question 6:** Approval criteria and business rules (critical for design)
2. ✅ **Question 18:** What does "10% loss" actually mean?
3. ✅ **Question 9:** Types of fraud encountered
4. ✅ **Question 13:** Current ERP system for integration
5. ✅ **Question 19:** What does success look like?
6. ✅ **Question 22:** Regulatory requirements for human approval

---

## Analysis & Observations

*This section will grow as we analyze the problem and develop insights.*

### Initial Observations:
- Manual process with 8 distinct steps
- Multiple points of potential failure/delay
- Heavy reliance on email and Excel for coordination
- Manual data entry into ERP system
- No automation in current workflow
- Customer notification required at each stage

### Opportunities Identified:
- [To be added as analysis progresses]

---

**Document Version:** 1.1
**Last Updated:** February 15, 2026
**Status:** Knowledge base with detailed questions for next KPMG session

**Recent Updates:**
- Added comprehensive question list for next session (30 questions organized by category)
- Defined solution approach: Human Approval Required for all credit decisions
- Recognized need to gather BancaFiel's approval criteria and business rules
- Prioritized 7 critical questions for 30-minute Session 2
