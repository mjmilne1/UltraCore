"""
Generate actual PDF Statement of Advice
Creates a real PDF file for UltraWealth Digital
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

def create_digital_soa_pdf():
    """Generate actual PDF SOA"""
    
    # Create filename with timestamp
    filename = f"UltraWealth_Digital_SOA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Create document
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=25*mm,
        bottomMargin=25*mm,
        title="Digital Statement of Advice - Sarah Thompson"
    )
    
    # Setup styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        name='CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    body_style = ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    # Build story
    story = []
    
    # Title Page
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph("<b>ULTRAWEALTH</b>", title_style))
    story.append(Paragraph("Digital Wealth Management", styles['Heading3']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("<b>STATEMENT OF ADVICE</b>", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Digital Notice Box
    notice_data = [[Paragraph(
        "<b>IMPORTANT: DIGITAL-ONLY SERVICE</b><br/><br/>"
        "This Statement of Advice has been prepared by automated systems "
        "without human adviser involvement. UltraWealth uses sophisticated "
        "algorithms and artificial intelligence to generate personalised advice.",
        body_style
    )]]
    
    notice_table = Table(notice_data, colWidths=[6.5*inch])
    notice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F7')),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#003366')),
        ('PADDING', (0, 0), (-1, -1), 12)
    ]))
    story.append(notice_table)
    
    story.append(Spacer(1, 0.5*inch))
    
    # Client Details
    client_data = [
        ["Prepared For:", "Sarah Thompson"],
        ["Date:", datetime.now().strftime("%d %B %Y")],
        ["Reference:", "DIG-SOA-2024-A7B3C9"],
        ["Valid Until:", datetime.now().strftime("%d %B %Y")]
    ]
    
    client_table = Table(client_data, colWidths=[2*inch, 4*inch])
    client_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTSIZE', (0, 0), (-1, -1), 10)
    ]))
    story.append(client_table)
    
    story.append(PageBreak())
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    summary_text = """
    Based on your digital assessment, we recommend establishing a Balanced Growth Portfolio 
    with an initial investment of $250,000. This portfolio targets returns of 7.8% p.a. 
    (after fees) with medium risk, suitable for your 10+ year investment horizon.
    """
    story.append(Paragraph(summary_text, body_style))
    
    # Key Recommendations
    story.append(Paragraph("<b>Key Recommendations:</b>", body_style))
    recommendations = [
        "Invest $250,000 in the Balanced Growth Portfolio",
        "Expected return of 7.8% p.a. after fees",
        "Total cost of just 0.70% p.a. (including ETF fees)",
        "Automatic rebalancing and tax optimization",
        "24/7 support from Anya AI assistant"
    ]
    
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", body_style))
    
    story.append(PageBreak())
    
    # Your Investment Portfolio
    story.append(Paragraph("YOUR RECOMMENDED PORTFOLIO", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>Balanced Growth Portfolio</b>", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Asset Allocation Table
    allocation_data = [
        ['Asset Class', 'Allocation', 'Purpose'],
        ['Australian Shares', '28%', 'Growth & Franking Credits'],
        ['International Shares', '27%', 'Global Diversification'],
        ['Emerging Markets', '5%', 'Higher Growth Potential'],
        ['Australian Bonds', '15%', 'Stability & Income'],
        ['International Bonds', '10%', 'Diversification'],
        ['Real Assets (REITs)', '10%', 'Inflation Protection'],
        ['Cash', '5%', 'Liquidity'],
        ['TOTAL', '100%', '']
    ]
    
    allocation_table = Table(allocation_data, colWidths=[2.2*inch, 1.3*inch, 2.5*inch])
    allocation_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E0E0E0')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(allocation_table)
    
    story.append(Spacer(1, 0.3*inch))
    
    # Expected Outcomes
    story.append(Paragraph("<b>Expected Outcomes:</b>", body_style))
    outcomes = [
        "Expected Return: 7.8% p.a. (after all fees)",
        "Expected Volatility: 12% p.a.",
        "Probability of Positive Return (1 year): 72%",
        "Probability of Positive Return (5 years): 91%"
    ]
    
    for outcome in outcomes:
        story.append(Paragraph(f"• {outcome}", body_style))
    
    story.append(PageBreak())
    
    # Fees Section
    story.append(Paragraph("SIMPLE, TRANSPARENT FEES", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("No hidden fees, no surprises:", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Fee Table
    fee_data = [
        ['Fee Type', 'Amount', 'When Charged'],
        ['Account Setup', '$0', 'Never'],
        ['Management Fee', '0.55% p.a.', 'Monthly'],
        ['Performance Fees', '$0', 'Never'],
        ['Exit Fees', '$0', 'Never'],
        ['Brokerage', 'Included', 'No extra charge']
    ]
    
    fee_table = Table(fee_data, colWidths=[2*inch, 2*inch, 2*inch])
    fee_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(fee_table)
    
    story.append(Spacer(1, 0.2*inch))
    
    # Annual cost calculation
    story.append(Paragraph("<b>Your Annual Costs:</b>", body_style))
    story.append(Paragraph("• Management Fee (0.55% × $250,000): $1,375", body_style))
    story.append(Paragraph("• ETF Costs (approximately 0.15%): $375", body_style))
    story.append(Paragraph("<b>• TOTAL: $1,750 per year (0.70%)</b>", body_style))
    
    story.append(PageBreak())
    
    # How We Manage Your Money
    story.append(Paragraph("HOW WE MANAGE YOUR PORTFOLIO", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    management_features = [
        ("<b>Automatic Rebalancing:</b>", "Your portfolio is automatically rebalanced when any asset class drifts 5% from target."),
        ("<b>Tax-Loss Harvesting:</b>", "Daily monitoring for opportunities to reduce your tax bill by harvesting losses."),
        ("<b>Dividend Reinvestment:</b>", "All dividends and distributions are automatically reinvested."),
        ("<b>Risk Monitoring:</b>", "Continuous monitoring ensures your portfolio stays aligned with your risk profile."),
        ("<b>Anya AI Support:</b>", "24/7 conversational AI assistant to answer your questions.")
    ]
    
    for feature, description in management_features:
        story.append(Paragraph(f"{feature} {description}", body_style))
    
    story.append(PageBreak())
    
    # Digital Advice Disclosure
    story.append(Paragraph("IMPORTANT INFORMATION ABOUT DIGITAL ADVICE", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    disclosure_text = """
    <b>How Our Algorithms Work:</b><br/><br/>
    UltraWealth uses sophisticated algorithms and machine learning to:
    • Assess your risk tolerance through our digital questionnaire
    • Construct optimal portfolios using Modern Portfolio Theory
    • Monitor and rebalance your portfolio automatically
    • Optimize for Australian tax efficiency
    • Provide personalized insights through Anya AI
    <br/><br/>
    <b>No Human Adviser:</b><br/>
    This is a fully digital service. No human financial adviser has reviewed 
    or approved your specific advice. Our algorithms are regularly tested and 
    audited to ensure they generate appropriate advice.
    """
    story.append(Paragraph(disclosure_text, body_style))
    
    story.append(PageBreak())
    
    # Risks Section
    story.append(Paragraph("UNDERSTANDING THE RISKS", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    risks = [
        ("<b>Market Risk:</b>", "The value of your investments can go down as well as up."),
        ("<b>Technology Risk:</b>", "System outages or errors could affect portfolio management."),
        ("<b>Model Risk:</b>", "Our algorithms are based on historical data which may not predict future outcomes."),
        ("<b>Liquidity Risk:</b>", "Some investments may be difficult to sell quickly."),
        ("<b>Currency Risk:</b>", "International investments are affected by exchange rate movements.")
    ]
    
    for risk_title, risk_desc in risks:
        story.append(Paragraph(f"{risk_title} {risk_desc}", body_style))
    
    story.append(PageBreak())
    
    # Next Steps
    story.append(Paragraph("NEXT STEPS", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("<b>Ready to proceed? Here's what happens next:</b>", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    steps = [
        "Review this Statement of Advice carefully",
        "Accept the advice online at app.ultrawealth.com.au",
        "Complete digital identity verification (5 minutes)",
        "Fund your account via BPAY or bank transfer",
        "We'll invest your money within 2 business days",
        "Monitor your portfolio 24/7 via web or mobile app"
    ]
    
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"<b>Step {i}:</b> {step}", body_style))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Support Information
    support_box_data = [[Paragraph(
        "<b>Need Help?</b><br/>"
        "• Anya AI: Available 24/7 in the app<br/>"
        "• Email: support@ultrawealth.com.au<br/>"
        "• Help Center: help.ultrawealth.com.au<br/>"
        "• Phone: 1300 ULTRA (business hours)",
        body_style
    )]]
    
    support_table = Table(support_box_data, colWidths=[6*inch])
    support_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9F9F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 10)
    ]))
    story.append(support_table)
    
    story.append(PageBreak())
    
    # Digital Consent
    story.append(Paragraph("DIGITAL CONSENT", heading_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#003366')))
    story.append(Spacer(1, 0.2*inch))
    
    consent_text = """
    <b>By accepting this advice online, you acknowledge that:</b><br/><br/>
    ☐ You have read and understood this Statement of Advice<br/>
    ☐ The information you provided is complete and accurate<br/>
    ☐ You understand the risks involved in investing<br/>
    ☐ You understand and accept all fees and costs<br/>
    ☐ You understand NO human adviser has reviewed this advice<br/>
    ☐ You accept the recommendations made by our algorithms<br/>
    ☐ You agree to receive ongoing service digitally<br/><br/>
    
    <b>To Accept:</b> Log into app.ultrawealth.com.au and click "Accept Statement of Advice"<br/><br/>
    
    <b>Client:</b> Sarah Thompson<br/>
    <b>Date:</b> {}<br/>
    <b>Reference:</b> DIG-SOA-2024-A7B3C9
    """.format(datetime.now().strftime("%d %B %Y"))
    
    story.append(Paragraph(consent_text, body_style))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Footer
    footer_text = """
    <b>UltraWealth Pty Ltd</b><br/>
    ABN 12 345 678 901 | AFSL 123456<br/>
    Level 20, 123 Collins Street, Melbourne VIC 3000<br/><br/>
    
    This document complies with ASIC RG 255 (Digital Financial Product Advice)<br/>
    Generated: {} | Valid for 30 days
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    story.append(Paragraph(footer_text, ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))
    
    # Build PDF
    doc.build(story)
    
    return filename

# Generate the PDF
print("\n" + "="*60)
print("  GENERATING DIGITAL STATEMENT OF ADVICE PDF")
print("="*60)

try:
    filename = create_digital_soa_pdf()
    
    # Get file size
    file_size = os.path.getsize(filename)
    
    print(f"\n✅ PDF GENERATED SUCCESSFULLY!")
    print(f"\n📄 File: {filename}")
    print(f"📊 Size: {file_size:,} bytes")
    print(f"📍 Location: {os.path.abspath(filename)}")
    print(f"\n🎯 The PDF is ready to open!")
    print(f"\n💡 To view: Open {filename} in any PDF reader")
    
except Exception as e:
    print(f"\n❌ Error generating PDF: {e}")
    print("\n💡 Make sure ReportLab is installed:")
    print("   pip install reportlab")

print("\n" + "="*60)
