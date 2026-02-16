#!/usr/bin/env python3
"""
Convert First Session Leadership Guide to PDF
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

def create_leadership_pdf():
    """Create a 2-page PDF from the leadership guide"""

    # Setup PDF
    pdf_path = "/Users/santiagocairesanchez/KPMG/personal_info/First_Session_Leadership_Guide.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.4*inch,
        bottomMargin=0.4*inch
    )

    # Container for elements
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=4,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=3
    )

    small_style = ParagraphStyle(
        'Small',
        parent=styles['BodyText'],
        fontSize=7,
        leading=8,
        textColor=colors.HexColor('#333333'),
        spaceAfter=2
    )

    # Title
    elements.append(Paragraph("First Session Leadership Guide", title_style))
    elements.append(Paragraph("<i>Personal Reference - Confidential</i>", small_style))
    elements.append(Spacer(1, 0.1*inch))

    # Session Structure
    elements.append(Paragraph("SESSION STRUCTURE (90-120 min)", heading_style))
    elements.append(Paragraph("• <b>Part 1 (15min):</b> Hand out briefing, 10min silent reading, \"This is ONE approach. We want YOUR input.\"", body_style))
    elements.append(Paragraph("• <b>Part 2 (30min):</b> Round-robin - each person 5-6min uninterrupted: What excites you? What concerns you? What to work on? Skills to learn?", body_style))
    elements.append(Paragraph("• <b>Part 3 (30min):</b> Open discussion - summarize themes, \"Should we explore alternatives or does AWS make sense?\"", body_style))
    elements.append(Paragraph("• <b>Part 4 (30min):</b> Work division - present roles, let team choose", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Proposed Roles
    elements.append(Paragraph("PROPOSED ROLE STRUCTURE", heading_style))

    role_data = [
        ['Person', 'Primary Role', 'Why It Matters'],
        ['You', 'Backend + Tech Lead', 'Architecture, Lambda, RDS, APIs'],
        ['Frontend', 'Frontend Dev', 'React app, UI/UX, dashboards'],
        ['Non-Tech #1', 'Project Manager', 'Timeline, standups - THE GLUE'],
        ['Non-Tech #2', 'Business Analyst', 'Cost/ROI analysis - KPMG CARES MOST'],
        ['Non-Tech #3', 'Change Mgmt', 'Training, presentation - DIFFERENTIATOR']
    ]

    role_table = Table(role_data, colWidths=[1.2*inch, 1.8*inch, 2.5*inch])
    role_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    elements.append(role_table)
    elements.append(Spacer(1, 0.08*inch))

    # Making People Feel Valued
    elements.append(Paragraph("MAKING NON-TECHNICAL PEOPLE FEEL VALUED", heading_style))
    elements.append(Paragraph("<b>To Business Analyst:</b> \"Business analysis is MORE important than code. KPMG cares about ROI, not Lambda. We trust YOUR numbers.\"", body_style))
    elements.append(Paragraph("<b>To Project Manager:</b> \"You're the captain. If we're behind, YOU decide what we cut. You keep us on track.\"", body_style))
    elements.append(Paragraph("<b>To Change Mgmt:</b> \"You're thinking like a consultant. Other teams will have tech. We'll have a REAL implementation strategy.\"", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Leadership Mantras
    elements.append(Paragraph("LEADERSHIP MANTRAS", heading_style))
    elements.append(Paragraph("1. <b>\"What do you think?\"</b> - Ask constantly | 2. <b>\"That's a great point.\"</b> - Validate input", body_style))
    elements.append(Paragraph("3. <b>\"How can we make sure everyone contributes?\"</b> - Show you care", body_style))
    elements.append(Paragraph("4. <b>\"Let's try it and adjust.\"</b> - Empower experimentation | 5. <b>\"We're all learning.\"</b> - Humble", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Sample Agenda
    elements.append(Paragraph("SAMPLE AGENDA", heading_style))
    agenda_text = """0:00-0:10 Welcome, briefing, reading | 0:10-0:15 Set tone | 0:15-0:45 Round-robin |
    0:45-1:00 Discussion | 1:00-1:15 BREAK | 1:15-1:30 Present roles | 1:30-1:45 Discussion |
    1:45-2:00 Assign roles | 2:00-2:15 Next steps | 2:15-2:30 Team dinner/social"""
    elements.append(Paragraph(agenda_text, small_style))
    elements.append(Spacer(1, 0.08*inch))

    # Team Organization
    elements.append(Paragraph("TEAM ORGANIZATION", heading_style))
    elements.append(Paragraph("❌ <b>Functional Teams:</b> Frontend/Backend/Business - Creates silos, business feels disconnected", body_style))
    elements.append(Paragraph("✅ <b>Feature Teams:</b> Squad 1 (Customer), Squad 2 (Analytics) - Cross-functional, see impact", body_style))
    elements.append(Paragraph("⭐ <b>Role-Based (BEST):</b> Clear ownership + daily collaboration through standups", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Red Flags
    elements.append(Paragraph("RED FLAGS TO AVOID", heading_style))
    elements.append(Paragraph("❌ \"Tech people build, business people write\" | ❌ \"Non-technical can test\" | ❌ \"Figure out roles later\"", body_style))
    elements.append(Paragraph("✅ Clear roles, clear value, clear collaboration", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Common Situations
    elements.append(Paragraph("HANDLING COMMON SITUATIONS", heading_style))
    elements.append(Paragraph("<b>\"I don't know AWS...\"</b> → \"That's okay! You research salaries, calculate ROI - critical for winning.\"", body_style))
    elements.append(Paragraph("<b>Wants to code but not technical:</b> → \"Great! Pair with frontend, do testing, learn React basics.\"", body_style))
    elements.append(Paragraph("<b>Technical wants to dominate:</b> → \"Love it! Let's make sure everyone has space. [Person], what do you think?\"", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Role Details
    elements.append(Paragraph("ROLE RESPONSIBILITIES DETAIL", heading_style))
    elements.append(Paragraph("<b>Project Manager:</b> Run standups, track timeline, manage deliverables, coordinate dev+business, presentations", small_style))
    elements.append(Paragraph("<b>Business Analyst:</b> Mexican salary research, ROI calculations, requirements gathering, quantitative analysis", small_style))
    elements.append(Paragraph("<b>Change Management:</b> How will BancaFiel adapt? Training strategy, communication plan, stakeholder analysis", small_style))
    elements.append(Spacer(1, 0.08*inch))

    # After Session
    elements.append(Paragraph("AFTER SESSION 1", heading_style))
    elements.append(Paragraph("Text each person: \"Thanks for input today! Excited to work with you on [role]. Questions welcome!\" - Creates psychological safety", body_style))
    elements.append(Spacer(1, 0.08*inch))

    # Key Success
    elements.append(Paragraph("KEY SUCCESS FACTORS", heading_style))
    elements.append(Paragraph("<b>Best teams aren't most technical - they're most COLLABORATIVE</b>", body_style))
    elements.append(Paragraph("Your leadership job: ✅ Make everyone feel heard | ✅ Give meaningful work | ✅ Create collaboration | ✅ Celebrate wins", body_style))
    elements.append(Spacer(1, 0.1*inch))

    # Remember
    elements.append(Paragraph("REMEMBER", heading_style))
    elements.append(Paragraph("The team wants to follow someone who: <b>Listens first • Values everyone • Creates clarity • Shows humility</b>", body_style))
    elements.append(Paragraph("<b>Be that leader today. You've got this! 🎯</b>", body_style))

    # Build PDF
    doc.build(elements)
    print(f"✅ PDF created successfully: {pdf_path}")

if __name__ == "__main__":
    create_leadership_pdf()
