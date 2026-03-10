from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# --- Page margins (narrow to fit 2 pages) ---
for section in doc.sections:
    section.top_margin    = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin   = Cm(2.0)
    section.right_margin  = Cm(2.0)

# --- Styles ---
ORANGE   = RGBColor(0xFF, 0x99, 0x00)
DARK     = RGBColor(0x0f, 0x17, 0x2a)
GRAY     = RGBColor(0x64, 0x74, 0x8b)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
BLUE     = RGBColor(0x1d, 0x4e, 0xd8)
TH_BG    = "FF9900"   # orange header fill
ROW_ALT  = "FFF7ED"   # light orange alt row

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_border(cell, border_color="E2E8F0"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ('top','left','bottom','right'):
        tag = OxmlElement(f'w:{"top" if edge=="top" else edge}')
        tag.set(qn('w:val'), 'single')
        tag.set(qn('w:sz'), '4')
        tag.set(qn('w:color'), border_color)
        tcPr.append(tag)

# ============================================================
# TITLE BLOCK
# ============================================================
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.LEFT
run = title.add_run("BancaFiel — Workflow & AWS Services")
run.bold = True
run.font.size = Pt(18)
run.font.color.rgb = DARK

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.LEFT
sub.paragraph_format.space_before = Pt(0)
sub.paragraph_format.space_after  = Pt(6)
r = sub.add_run("Version: March 2026  ·  Stack: AWS Serverless  ·  Region: us-east-1")
r.font.size = Pt(9)
r.font.color.rgb = GRAY

# Divider line via bottom border on paragraph
from docx.oxml import OxmlElement as OE
pPr = sub._p.get_or_add_pPr()
pBdr = OE('w:pBdr')
bottom = OE('w:bottom')
bottom.set(qn('w:val'), 'single')
bottom.set(qn('w:sz'), '6')
bottom.set(qn('w:space'), '4')
bottom.set(qn('w:color'), 'FF9900')
pBdr.append(bottom)
pPr.append(pBdr)

# ============================================================
# SECTION 1
# ============================================================
def section_heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(3)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = ORANGE

def phase_heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(5)
    p.paragraph_format.space_after  = Pt(2)
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(10)
    r.font.color.rgb = DARK

def lambda_entry(label, body):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.left_indent  = Inches(0.2)
    r1 = p.add_run(label + " — ")
    r1.bold = True
    r1.font.size = Pt(9)
    r1.font.color.rgb = DARK
    r2 = p.add_run(body)
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

section_heading("1. How the System Works (End-to-End)")

# Architecture diagram
try:
    img_para = doc.add_paragraph()
    img_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_para.paragraph_format.space_before = Pt(2)
    img_para.paragraph_format.space_after  = Pt(4)
    run_img = img_para.add_run()
    run_img.add_picture("/Users/santiagocairesanchez/KPMG/bancafiel_architecture.png", width=Inches(6.3))
except Exception as e:
    print(f"Warning: could not embed image: {e}")

phase_heading("Entry Point")
p = doc.add_paragraph()
p.paragraph_format.space_after = Pt(2)
p.paragraph_format.left_indent = Inches(0.2)
r = p.add_run(
    "A client submits a loan application through www.bancafiel.com by uploading their INE (national ID) "
    "and proof of address. These files land in an S3 bucket, which automatically triggers the pipeline. "
    "Clients also use a REST API to check status, register, and log in."
)
r.font.size = Pt(9)
r.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

phase_heading("Phase 1 — Document Intelligence (Lambdas 1–3)")
lambda_entry("Lambda 1 · processDocument",
    "Triggered on S3 upload. Sends the document to Claude Sonnet via Amazon Bedrock for AI-powered OCR. "
    "Saves extracted fields to the database and asynchronously triggers Lambda 2.")
lambda_entry("Lambda 2 · extractData",
    "Verifies the Bedrock output is complete and well-structured, organizes fields by document type "
    "(name, CURP, address, DOB), then asynchronously triggers Lambda 3.")
lambda_entry("Lambda 3 · validateData",
    "Core validation step. Validates all fields, links the customer via their CURP, creates or finds "
    "the customer record in PostgreSQL, and sends the applicant a confirmation email. "
    "Only triggers Lambda 4 on the INE document to prevent the pipeline from running twice.")

phase_heading("Phase 2 — Fraud Detection (Lambda 4)")
lambda_entry("Lambda 4 · detectFraud",
    "Runs a custom rule-based fraud scoring algorithm checking: debt-to-income ratio, age from CURP, "
    "ID consistency, duplicate applications, and blacklists. Assigns a risk level — "
    "HIGH → auto-reject; MEDIUM/LOW → analyst review via Step Functions.")

phase_heading("Phase 3 — Approval Workflow (Step Functions + Lambda 5)")
lambda_entry("Step Functions · Loan Workflow",
    "Orchestrates the human-in-the-loop approval. Routes the case based on fraud risk and waits for "
    "the analyst's decision.")
lambda_entry("Lambda 5 · approvalNotifier",
    "Sends an HTML email to the analyst with full application details, fraud score, and Approve/Reject "
    "buttons that call the REST API.")

phase_heading("Phase 4 — Decision & Notification (Lambdas 6–7)")
lambda_entry("Lambda 6 · erpUpdater",
    "Updates the application status in PostgreSQL and writes a full audit log entry. "
    "Asynchronously invokes Lambda 7.")
lambda_entry("Lambda 7 · notificationSender",
    "Sends the applicant their result via Amazon SES using HTML email templates: "
    "received confirmation, approval, or rejection.")

# ============================================================
# SECTION 2 — Services Table
# ============================================================
section_heading("2. AWS Services Used")

services = [
    ("AWS Lambda",                  "Runs all 7 pipeline steps + REST API handlers — executes only when triggered, zero idle cost"),
    ("AWS Step Functions",          "Orchestrates the analyst approval flow — routes HIGH/MEDIUM/LOW fraud risk to the correct path"),
    ("Amazon S3",                   "Stores uploaded loan documents — triggers the pipeline automatically on every upload"),
    ("Amazon RDS (PostgreSQL)",     "Single source of truth — applications, customers, fraud scores, audit history, login accounts"),
    ("Amazon Bedrock (Claude)",     "AI-powered OCR — reads and extracts structured data from ID documents"),
    ("Amazon API Gateway",          "Exposes the REST API to the frontend — handles all HTTP requests from both portals"),
    ("Amazon CloudFront",           "Serves www.bancafiel.com and analyst.bancafiel.com globally with low latency"),
    ("Amazon SES",                  "Sends all transactional HTML emails — received, approved, and rejected notifications"),
    ("AWS IAM",                     "Enforces least-privilege access — each Lambda only calls the exact services it needs"),
    ("AWS ACM",                     "Manages the SSL/TLS certificate for all three domains — enforces HTTPS everywhere"),
    ("CloudFront OAC",              "Locks S3 so files can only be served through CloudFront — raw S3 URLs are blocked"),
    ("AWS SAM",                     "Defines and deploys the entire backend from a single YAML file — one command to deploy"),
    ("AWS CloudFormation",          "Underlying engine used by SAM — manages all resources as a single versioned stack"),
]

table = doc.add_table(rows=1, cols=2)
table.style = 'Table Grid'
table.alignment = WD_TABLE_ALIGNMENT.LEFT

# Column widths
table.columns[0].width = Cm(4.8)
table.columns[1].width = Cm(12.0)

# Header row
hdr = table.rows[0].cells
hdr[0].text = "Service"
hdr[1].text = "Role in BancaFiel"
for i, cell in enumerate(hdr):
    set_cell_bg(cell, TH_BG)
    for para in cell.paragraphs:
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in para.runs:
            run.bold = True
            run.font.size = Pt(9)
            run.font.color.rgb = WHITE

# Data rows
for idx, (svc, desc) in enumerate(services):
    row = table.add_row().cells
    row[0].text = svc
    row[1].text = desc
    fill = ROW_ALT if idx % 2 == 0 else "FFFFFF"
    set_cell_bg(row[0], fill)
    set_cell_bg(row[1], fill)
    for cell in row:
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = DARK
        cell.paragraphs[0].paragraph_format.space_before = Pt(2)
        cell.paragraphs[0].paragraph_format.space_after  = Pt(2)
    row[0].paragraphs[0].runs[0].bold = True

# Footer note
footer = doc.add_paragraph()
footer.paragraph_format.space_before = Pt(6)
r = footer.add_run(
    "Total: 13 AWS services — the same stack trusted by Netflix, Airbnb, Apple, Disney, NASA, "
    "and 60% of the Fortune 500."
)
r.italic = True
r.font.size = Pt(8.5)
r.font.color.rgb = GRAY

out = "/Users/santiagocairesanchez/KPMG/docs/technical/BancaFiel_Workflow_and_Services.docx"
doc.save(out)
print(f"Saved: {out}")
