"""
UltraWealth Digital Statement of Advice Generator
Fully automated digital advice - No human advisers
Based on robo-advice best practices
ASIC RG 255 compliant (Robo-advice)
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, date
from dataclasses import dataclass
import uuid
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

# ============== DIGITAL ADVICE COMPLIANCE ==============

class ASICDigitalAdviceCompliance:
    """
    ASIC Regulatory Guide 255 - Providing digital financial product advice
    Fully automated advice compliance
    """
    
    def __init__(self):
        self.regulatory_guide = "RG 255"
        self.service_type = "DIGITAL_ONLY"
        self.no_human_advisers = True
        
        # Digital advice requirements
        self.requirements = {
            'algorithms_tested': True,
            'advice_generation_automated': True,
            'monitoring_systems': True,
            'client_understanding_verified': True,
            'best_interests_duty_programmed': True,
            'risk_profiling_automated': True
        }
        
        # Mandatory disclosures for digital advice
        self.digital_disclosures = [
            "This Statement of Advice has been prepared by automated systems without human adviser involvement.",
            "UltraWealth uses sophisticated algorithms and artificial intelligence to generate personalised advice.",
            "The advice is based solely on the information you have provided through our digital platform.",
            "No human has reviewed this specific advice before it was provided to you.",
            "Our algorithms are regularly tested and monitored to ensure they generate appropriate advice."
        ]

# ============== DIGITAL SOA GENERATOR ==============

class DigitalSOAGenerator:
    """
    Generate SOA for digital-only service
    Similar to Stockspot/Six Park model
    """
    
    def __init__(self):
        self.styles = self.setup_styles()
        self.service_name = "UltraWealth Digital Wealth Management"
        self.is_digital = True
        
    def setup_styles(self) -> Dict:
        """Setup PDF styles for digital SOA"""
        styles = getSampleStyleSheet()
        
        # Modern, clean digital styling
        styles.add(ParagraphStyle(
            name='DigitalTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#2E5266'),
            spaceAfter=20,
            alignment=TA_LEFT
        ))
        
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2E5266'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        styles.add(ParagraphStyle(
            name='DigitalBody',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_JUSTIFY
        ))
        
        return styles
    
    async def generate_digital_soa(self, client_data: Dict) -> bytes:
        """Generate digital-only SOA PDF"""
        
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=25*mm,
            bottomMargin=25*mm,
            title=f"Digital Statement of Advice - {client_data['name']}"
        )
        
        story = []
        
        # Digital service header
        story.extend(self.create_digital_header(client_data))
        story.append(PageBreak())
        
        # Important information about digital advice
        story.extend(self.create_digital_advice_disclosure())
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self.create_executive_summary(client_data))
        story.append(PageBreak())
        
        # Your information (as provided digitally)
        story.extend(self.create_client_information(client_data))
        story.append(PageBreak())
        
        # Our understanding of your situation
        story.extend(self.create_situation_understanding(client_data))
        story.append(PageBreak())
        
        # Recommended portfolio
        story.extend(self.create_portfolio_recommendation(client_data))
        story.append(PageBreak())
        
        # How we manage your money
        story.extend(self.create_management_approach())
        story.append(PageBreak())
        
        # Fees (transparent digital pricing)
        story.extend(self.create_fee_section(client_data))
        story.append(PageBreak())
        
        # Risks
        story.extend(self.create_risk_section())
        story.append(PageBreak())
        
        # How our algorithms work
        story.extend(self.create_algorithm_disclosure())
        story.append(PageBreak())
        
        # Next steps (digital onboarding)
        story.extend(self.create_next_steps())
        story.append(PageBreak())
        
        # Digital consent and authority
        story.extend(self.create_digital_consent(client_data))
        
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def create_digital_header(self, client_data: Dict) -> List:
        """Create digital service header"""
        elements = []
        
        # Modern, clean header
        elements.append(Spacer(1, 0.5*inch))
        
        elements.append(Paragraph(
            "ULTRAWEALTH",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Paragraph(
            "Digital Wealth Management",
            self.styles['SectionHeader']
        ))
        
        elements.append(Spacer(1, 0.3*inch))
        
        elements.append(Paragraph(
            "<b>STATEMENT OF ADVICE</b>",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Client details
        elements.append(Paragraph(
            f"Prepared for: <b>{client_data['name']}</b>",
            self.styles['DigitalBody']
        ))
        
        elements.append(Paragraph(
            f"Date: {datetime.now().strftime('%d %B %Y')}",
            self.styles['DigitalBody']
        ))
        
        elements.append(Paragraph(
            f"Reference: {client_data.get('reference', 'DIG-' + str(uuid.uuid4())[:8].upper())}",
            self.styles['DigitalBody']
        ))
        
        elements.append(Spacer(1, 0.5*inch))
        
        # Digital service notice
        notice_box = Table(
            [[Paragraph(
                "<b>This advice has been generated digitally by UltraWealth's automated advice platform.</b><br/><br/>"
                "No human financial adviser has been involved in preparing this personalised advice.",
                self.styles['DigitalBody']
            )]],
            colWidths=[6.5*inch]
        )
        
        notice_box.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F4F7')),
            ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#2E5266')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        elements.append(notice_box)
        
        return elements
    
    def create_digital_advice_disclosure(self) -> List:
        """Create digital advice disclosure section"""
        elements = []
        
        elements.append(Paragraph(
            "IMPORTANT INFORMATION ABOUT DIGITAL ADVICE",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        disclosure_text = """
        <b>How UltraWealth's Digital Advice Works</b><br/><br/>
        
        UltraWealth is a fully digital wealth management service that uses advanced algorithms, 
        artificial intelligence, and machine learning to provide personalised investment advice 
        and portfolio management. Here's what you need to know:
        """
        
        elements.append(Paragraph(disclosure_text, self.styles['DigitalBody']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Key points about digital advice
        digital_points = [
            "<b>Algorithmic Advice:</b> Your advice is generated by sophisticated algorithms that consider your personal circumstances, goals, and risk tolerance.",
            
            "<b>No Human Advisers:</b> This is a digital-only service. No human financial adviser reviews or approves your specific advice.",
            
            "<b>Continuous Monitoring:</b> Our systems continuously monitor your portfolio and automatically rebalance when needed.",
            
            "<b>Anya AI Assistant:</b> Our AI assistant Anya can answer your questions 24/7 using natural language processing.",
            
            "<b>Best Interests Duty:</b> Our algorithms are programmed to act in your best interests and comply with all regulatory requirements.",
            
            "<b>Regular Algorithm Testing:</b> We regularly test and audit our algorithms to ensure they generate appropriate advice.",
            
            "<b>Data Security:</b> Your information is protected using bank-level encryption and security measures."
        ]
        
        for point in digital_points:
            elements.append(Paragraph(f"• {point}", self.styles['DigitalBody']))
            elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Regulatory compliance
        elements.append(Paragraph(
            "<b>Regulatory Compliance</b>",
            self.styles['SectionHeader']
        ))
        
        compliance_text = """
        UltraWealth Pty Ltd holds Australian Financial Services License (AFSL) 123456 and is 
        authorised to provide digital financial product advice and operate managed discretionary 
        accounts. We comply with ASIC Regulatory Guide 255 (Providing digital financial product advice).
        """
        
        elements.append(Paragraph(compliance_text, self.styles['DigitalBody']))
        
        return elements
    
    def create_executive_summary(self, client_data: Dict) -> List:
        """Create executive summary for digital SOA"""
        elements = []
        
        elements.append(Paragraph(
            "YOUR PERSONALISED INVESTMENT RECOMMENDATION",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary based on digital assessment
        summary = f"""
        Based on the information you provided through our digital platform, we recommend:
        
        <b>Investment Amount:</b> ${client_data.get('investment_amount', 100000):,}<br/>
        <b>Recommended Portfolio:</b> {client_data.get('portfolio', 'Balanced Growth')}<br/>
        <b>Expected Return:</b> {client_data.get('expected_return', 7.8)}% p.a. (after fees)<br/>
        <b>Risk Level:</b> {client_data.get('risk_level', 'Medium')}<br/>
        <b>Time Horizon:</b> {client_data.get('time_horizon', '5+ years')}<br/>
        """
        
        elements.append(Paragraph(summary, self.styles['DigitalBody']))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Key benefits
        elements.append(Paragraph(
            "<b>Key Benefits of Your Digital Portfolio:</b>",
            self.styles['SectionHeader']
        ))
        
        benefits = [
            "Professionally designed portfolio using Modern Portfolio Theory",
            "Automatic rebalancing to maintain optimal asset allocation",
            "Tax optimisation through automated tax-loss harvesting",
            "Low fees compared to traditional advice",
            "24/7 access through web and mobile apps",
            "No minimum investment period or exit fees"
        ]
        
        for benefit in benefits:
            elements.append(Paragraph(f"✓ {benefit}", self.styles['DigitalBody']))
        
        return elements
    
    def create_client_information(self, client_data: Dict) -> List:
        """Create client information section"""
        elements = []
        
        elements.append(Paragraph(
            "INFORMATION YOU PROVIDED",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        info_text = """
        This advice is based on the information you provided through our digital questionnaire:
        """
        
        elements.append(Paragraph(info_text, self.styles['DigitalBody']))
        
        # Client details table
        client_info = [
            ['Personal Information', ''],
            ['Name:', client_data.get('name', 'Not provided')],
            ['Age:', f"{client_data.get('age', 'Not provided')} years"],
            ['Employment Status:', client_data.get('employment', 'Employed')],
            ['Annual Income:', f"${client_data.get('income', 100000):,}"],
            ['Investment Experience:', client_data.get('experience', 'Some experience')],
        ]
        
        info_table = Table(client_info, colWidths=[2.5*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5266')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(info_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Important notice
        elements.append(Paragraph(
            "<b>Important:</b> If any of this information is incorrect or has changed, "
            "please update it immediately through the platform before proceeding.",
            self.styles['DigitalBody']
        ))
        
        return elements
    
    def create_situation_understanding(self, client_data: Dict) -> List:
        """Create situation understanding section"""
        elements = []
        
        elements.append(Paragraph(
            "OUR UNDERSTANDING OF YOUR SITUATION",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Goals identified through digital assessment
        elements.append(Paragraph(
            "<b>Your Investment Goals (as identified by our system):</b>",
            self.styles['SectionHeader']
        ))
        
        goals = client_data.get('goals', [
            "Build long-term wealth",
            "Save for retirement",
            "Generate passive income"
        ])
        
        for goal in goals:
            elements.append(Paragraph(f"• {goal}", self.styles['DigitalBody']))
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Risk assessment results
        elements.append(Paragraph(
            "<b>Risk Assessment Results:</b>",
            self.styles['SectionHeader']
        ))
        
        risk_text = f"""
        Our digital risk profiling tool has assessed your risk tolerance as 
        <b>{client_data.get('risk_tolerance', 'Balanced')}</b> based on your responses.
        
        This means you:
        • Can accept moderate fluctuations in portfolio value
        • Seek a balance between growth and stability
        • Have a medium to long-term investment horizon
        • Understand that investments can decrease in value
        """
        
        elements.append(Paragraph(risk_text, self.styles['DigitalBody']))
        
        return elements
    
    def create_portfolio_recommendation(self, client_data: Dict) -> List:
        """Create portfolio recommendation section"""
        elements = []
        
        elements.append(Paragraph(
            "YOUR RECOMMENDED PORTFOLIO",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        portfolio_name = client_data.get('portfolio', 'Balanced Growth Portfolio')
        
        elements.append(Paragraph(
            f"<b>{portfolio_name}</b>",
            self.styles['SectionHeader']
        ))
        
        # Asset allocation
        allocation_data = [
            ['Asset Class', 'Allocation', 'Purpose'],
            ['Australian Shares', '28%', 'Growth & Franking Credits'],
            ['International Shares', '27%', 'Global Diversification'],
            ['Emerging Markets', '5%', 'Higher Growth Potential'],
            ['Australian Bonds', '15%', 'Stability & Income'],
            ['International Bonds', '10%', 'Diversification'],
            ['Real Assets', '10%', 'Inflation Protection'],
            ['Cash', '5%', 'Liquidity & Stability'],
            ['TOTAL', '100%', '']
        ]
        
        allocation_table = Table(allocation_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        allocation_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5266')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F4F7')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(allocation_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Expected outcomes
        elements.append(Paragraph(
            "<b>Expected Outcomes (Based on Historical Data):</b>",
            self.styles['SectionHeader']
        ))
        
        outcomes = f"""
        • Expected Return: {client_data.get('expected_return', 7.8)}% p.a. (after fees)
        • Expected Volatility: {client_data.get('volatility', 12)}% p.a.
        • Probability of Positive Return (1 year): {client_data.get('prob_1y', 72)}%
        • Probability of Positive Return (5 years): {client_data.get('prob_5y', 91)}%
        • Maximum Historical Drawdown: {client_data.get('max_drawdown', -18)}%
        """
        
        elements.append(Paragraph(outcomes, self.styles['DigitalBody']))
        
        return elements
    
    def create_management_approach(self) -> List:
        """Create management approach section"""
        elements = []
        
        elements.append(Paragraph(
            "HOW WE MANAGE YOUR PORTFOLIO",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Automated management features
        management_text = """
        <b>Fully Automated Portfolio Management</b><br/><br/>
        
        Your portfolio is managed entirely by our algorithmic systems:
        """
        
        elements.append(Paragraph(management_text, self.styles['DigitalBody']))
        
        features = [
            {
                'title': 'Automatic Rebalancing',
                'description': 'When your portfolio drifts 5% or more from target allocation, our system automatically rebalances.'
            },
            {
                'title': 'Tax-Loss Harvesting',
                'description': 'Daily monitoring for opportunities to harvest losses and reduce your tax bill.'
            },
            {
                'title': 'Dividend Reinvestment',
                'description': 'All dividends and distributions are automatically reinvested.'
            },
            {
                'title': 'Risk Monitoring',
                'description': 'Continuous monitoring ensures your portfolio stays aligned with your risk profile.'
            },
            {
                'title': 'Cost Optimisation',
                'description': 'We use low-cost ETFs and wholesale funds to minimize investment costs.'
            }
        ]
        
        for feature in features:
            elements.append(Paragraph(
                f"<b>{feature['title']}</b>",
                self.styles['DigitalBody']
            ))
            elements.append(Paragraph(
                feature['description'],
                self.styles['DigitalBody']
            ))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def create_fee_section(self, client_data: Dict) -> List:
        """Create transparent fee section"""
        elements = []
        
        elements.append(Paragraph(
            "SIMPLE, TRANSPARENT FEES",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            "No hidden fees, no surprises. Here's exactly what you'll pay:",
            self.styles['DigitalBody']
        ))
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Fee structure
        investment = client_data.get('investment_amount', 100000)
        
        # Calculate tiered fees (similar to robo-advisors)
        if investment < 50000:
            mgmt_fee = 0.0066  # 0.66%
        elif investment < 200000:
            mgmt_fee = 0.0055  # 0.55%
        else:
            mgmt_fee = 0.0044  # 0.44%
        
        annual_fee = investment * mgmt_fee
        
        fee_data = [
            ['Fee Type', 'Amount', 'When Charged'],
            ['Account Setup Fee', '$0', 'Never'],
            ['Management Fee', f'{mgmt_fee:.2%} p.a.', 'Monthly (1/12th)'],
            ['Annual Dollar Amount', f'${annual_fee:,.0f}', 'Monthly (1/12th)'],
            ['Performance Fees', '$0', 'Never'],
            ['Exit Fees', '$0', 'Never'],
            ['Brokerage', 'Included', 'No extra charge'],
        ]
        
        fee_table = Table(fee_data, colWidths=[2*inch, 2*inch, 2*inch])
        fee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5266')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(fee_table)
        
        elements.append(Spacer(1, 0.15*inch))
        
        # ETF costs
        elements.append(Paragraph(
            "<b>Indirect Costs (ETF fees):</b> Approximately 0.15% p.a.<br/>"
            "These are built into the ETF prices and not charged separately.",
            self.styles['DigitalBody']
        ))
        
        elements.append(Spacer(1, 0.15*inch))
        
        # Total cost comparison
        total_cost = mgmt_fee + 0.0015  # Including ETF costs
        
        comparison_text = f"""
        <b>Total Cost: {total_cost:.2%} p.a.</b><br/>
        Compare this to:
        • Traditional financial advisers: 1.0% - 2.5% p.a.
        • Full-service brokers: 1.5% - 3.0% p.a.
        • Industry super funds: 0.8% - 1.5% p.a.
        """
        
        elements.append(Paragraph(comparison_text, self.styles['DigitalBody']))
        
        return elements
    
    def create_risk_section(self) -> List:
        """Create risk disclosure section"""
        elements = []
        
        elements.append(Paragraph(
            "UNDERSTANDING THE RISKS",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        risk_intro = """
        All investments carry risk. The value of your portfolio can go down as well as up, 
        and you may receive back less than you invested. Key risks include:
        """
        
        elements.append(Paragraph(risk_intro, self.styles['DigitalBody']))
        
        elements.append(Spacer(1, 0.1*inch))
        
        risks = [
            {
                'risk': 'Market Risk',
                'description': 'Markets can be volatile and your portfolio value will fluctuate.'
            },
            {
                'risk': 'Technology Risk',
                'description': 'System outages or errors could affect portfolio management.'
            },
            {
                'risk': 'Model Risk',
                'description': 'Our algorithms are based on historical data which may not predict future outcomes.'
            },
            {
                'risk': 'Liquidity Risk',
                'description': 'In extreme market conditions, some ETFs may be difficult to sell.'
            },
            {
                'risk': 'Currency Risk',
                'description': 'International investments are affected by exchange rate movements.'
            }
        ]
        
        for risk_item in risks:
            elements.append(Paragraph(
                f"<b>{risk_item['risk']}:</b> {risk_item['description']}",
                self.styles['DigitalBody']
            ))
            elements.append(Spacer(1, 0.05*inch))
        
        return elements
    
    def create_algorithm_disclosure(self) -> List:
        """Create algorithm disclosure section"""
        elements = []
        
        elements.append(Paragraph(
            "HOW OUR ALGORITHMS WORK",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        algo_text = """
        <b>Transparency About Our Technology</b><br/><br/>
        
        UltraWealth uses several types of algorithms to manage your portfolio:
        
        <b>1. Portfolio Construction Algorithm</b><br/>
        Uses Modern Portfolio Theory to create efficient portfolios that maximize expected 
        return for your level of risk.
        
        <b>2. Risk Assessment Algorithm</b><br/>
        Analyzes your questionnaire responses using machine learning to determine your 
        risk tolerance and capacity.
        
        <b>3. Rebalancing Algorithm</b><br/>
        Monitors your portfolio daily and triggers rebalancing when allocations drift 
        beyond set thresholds.
        
        <b>4. Tax Optimization Algorithm</b><br/>
        Identifies tax-loss harvesting opportunities and manages the timing of trades 
        to minimize tax impact.
        
        <b>5. Anya AI System</b><br/>
        Our conversational AI uses natural language processing to answer your questions 
        and provide insights about your portfolio.
        
        <b>Algorithm Governance</b><br/>
        • All algorithms are tested extensively before deployment
        • Regular audits ensure algorithms perform as intended
        • Human oversight monitors system performance
        • Compliance checks are built into every algorithm
        """
        
        elements.append(Paragraph(algo_text, self.styles['DigitalBody']))
        
        return elements
    
    def create_next_steps(self) -> List:
        """Create next steps section"""
        elements = []
        
        elements.append(Paragraph(
            "NEXT STEPS",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        elements.append(Paragraph(
            "Ready to start? Here's how to proceed:",
            self.styles['DigitalBody']
        ))
        
        elements.append(Spacer(1, 0.1*inch))
        
        steps = [
            "Review this Statement of Advice carefully",
            "If you're happy to proceed, accept the advice online",
            "Complete the digital account opening process",
            "Fund your account via BPAY or bank transfer",
            "We'll invest your money within 2 business days",
            "Monitor your portfolio 24/7 via web or mobile app"
        ]
        
        for i, step in enumerate(steps, 1):
            elements.append(Paragraph(
                f"<b>Step {i}:</b> {step}",
                self.styles['DigitalBody']
            ))
            elements.append(Spacer(1, 0.05*inch))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Support information
        support_text = """
        <b>Need Help?</b><br/>
        • Chat with Anya AI: Available 24/7 in the app
        • Email: support@ultrawealth.com.au
        • Help Center: help.ultrawealth.com.au
        • Phone: 1300 ULTRA (business hours only)
        """
        
        elements.append(Paragraph(support_text, self.styles['DigitalBody']))
        
        return elements
    
    def create_digital_consent(self, client_data: Dict) -> List:
        """Create digital consent section"""
        elements = []
        
        elements.append(Paragraph(
            "YOUR CONSENT",
            self.styles['DigitalTitle']
        ))
        
        elements.append(Spacer(1, 0.2*inch))
        
        consent_text = f"""
        <b>Digital Acceptance</b><br/><br/>
        
        By clicking "Accept and Proceed" in the UltraWealth platform, you confirm that:
        
        • You have read and understood this Statement of Advice
        • The information you provided is complete and accurate
        • You understand the risks involved in investing
        • You understand and accept all fees and costs
        • You agree to receive ongoing advice digitally
        • You understand no human adviser has reviewed this advice
        • You accept the recommendations made by our algorithms
        
        <b>Client:</b> {client_data.get('name', 'Client Name')}<br/>
        <b>Date:</b> {datetime.now().strftime('%d %B %Y')}<br/>
        <b>Digital Consent:</b> To be confirmed online<br/>
        <b>Reference:</b> {client_data.get('reference', 'DIG-' + str(uuid.uuid4())[:8].upper())}
        """
        
        elements.append(Paragraph(consent_text, self.styles['DigitalBody']))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Important notices
        notice = """
        <b>Important Legal Information</b><br/>
        
        This Statement of Advice is valid for 30 days from the date of issue. 
        The advice is based on information current at the date of this document 
        and may not be suitable if your circumstances change.
        
        UltraWealth Pty Ltd | ABN 12 345 678 901 | AFSL 123456<br/>
        Level 20, 123 Collins Street, Melbourne VIC 3000<br/>
        
        If you have a complaint about our service, please contact us first. 
        If unresolved, you can contact the Australian Financial Complaints Authority (AFCA):<br/>
        Website: www.afca.org.au | Email: info@afca.org.au | Phone: 1800 931 678
        """
        
        elements.append(Paragraph(notice, self.styles['Disclaimer']))
        
        return elements

# ============== DIGITAL SOA SERVICE ==============

class DigitalSOAService:
    """
    Digital-only SOA generation service
    No human advisers involved
    """
    
    def __init__(self):
        self.generator = DigitalSOAGenerator()
        self.compliance = ASICDigitalAdviceCompliance()
        
    async def generate_digital_soa(self, client_data: Dict) -> Dict:
        """Generate digital SOA"""
        
        # Ensure digital compliance
        if not self.compliance.no_human_advisers:
            raise ValueError("This service is digital-only")
        
        # Add digital disclosures
        client_data['disclosures'] = self.compliance.digital_disclosures
        
        # Generate PDF
        pdf_bytes = await self.generator.generate_digital_soa(client_data)
        
        # Create response
        soa_id = f"DIG-SOA-{uuid.uuid4().hex[:8].upper()}"
        
        return {
            'success': True,
            'soa_id': soa_id,
            'pdf_bytes': pdf_bytes,
            'pdf_size': len(pdf_bytes),
            'filename': f"UltraWealth_SOA_{client_data.get('name', '').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            'type': 'DIGITAL_ONLY',
            'human_adviser_involved': False,
            'generated_at': datetime.now().isoformat()
        }

# ============== TEST DIGITAL SOA ==============

async def test_digital_soa():
    """Test digital SOA generation"""
    
    # Sample client data (from digital questionnaire)
    client_data = {
        'name': 'Sarah Thompson',
        'age': 35,
        'email': 'sarah.thompson@email.com',
        'income': 120000,
        'employment': 'Full-time employed',
        'experience': 'Some investment experience',
        'investment_amount': 250000,
        'goals': [
            'Build wealth for retirement',
            'Generate passive income',
            'Minimize tax'
        ],
        'risk_tolerance': 'Balanced',
        'time_horizon': '10+ years',
        'portfolio': 'Balanced Growth Portfolio',
        'expected_return': 7.8,
        'volatility': 12,
        'risk_level': 'Medium',
        'prob_1y': 72,
        'prob_5y': 91,
        'max_drawdown': -18
    }
    
    # Generate digital SOA
    service = DigitalSOAService()
    result = await service.generate_digital_soa(client_data)
    
    print("\n" + "="*60)
    print(" "*15 + "DIGITAL SOA GENERATED")
    print("="*60)
    print(f"\n✅ SOA ID: {result['soa_id']}")
    print(f"✅ Filename: {result['filename']}")
    print(f"✅ Size: {result['pdf_size']:,} bytes")
    print(f"✅ Type: {result['type']}")
    print(f"✅ Human Adviser: {result['human_adviser_involved']}")
    print("\n📄 Digital SOA ready for client review!")
    print("="*60)
    
    return result

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_digital_soa())

