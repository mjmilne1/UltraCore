"""Anya - AI Lending Assistant (OpenAI)"""
from typing import Dict, Any, Optional
from decimal import Decimal
import json

from openai import AsyncOpenAI

from ultracore.anya.agent import AnyaAgent
from ..origination import LoanApplicationService


class AnyaLendingAgent(AnyaAgent):
    """
    Anya's Lending specialist powered by OpenAI.
    
    Natural language interface for:
    - "I need a $20,000 personal loan for debt consolidation"
    - "How much can I borrow for a home loan?"
    - "What's the interest rate on a business loan?"
    - "Can I get a loan if my credit score is 650?"
    - "Explain comparison rates"
    - "What documents do I need?"
    
    Australian lending expertise:
    - NCCP responsible lending
    - Credit scoring and approval
    - Comparison rates
    - LVR calculations
    - Loan products and features
    - Application process guidance
    """
    
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        application_service: LoanApplicationService = None,
        customer_id: str = None
    ):
        super().__init__(
            name="AnyaLendingAgent",
            description="AI lending assistant for loan applications",
            capabilities=[
                "Loan pre-qualification",
                "Product recommendations",
                "Application guidance",
                "Credit advice",
                "Document requirements",
                "Rate explanations",
                "Affordability calculations"
            ]
        )
        
        self.openai = openai_client
        self.application_service = application_service
        self.customer_id = customer_id
    
    async def execute(
        self,
        natural_language_request: str
    ) -> Dict[str, Any]:
        """Process lending-related request."""
        
        context = await self._build_context()
        prompt = self._build_prompt(natural_language_request, context)
        
        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            parsed = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {
                "success": True,
                "message": response.choices[0].message.content
            }
        
        return await self._execute_intent(parsed)
    
    def _get_system_prompt(self) -> str:
        """System prompt for Anya as lending expert."""
        return """You are Anya, a friendly AI lending assistant specializing in Australian loans.

Your role is to help customers:
1. Understand loan products (personal, home, business, LOC, BNPL)
2. Get pre-qualified for loans
3. Navigate the application process
4. Understand credit scoring and approval
5. Learn about rates, fees, and comparison rates
6. Prepare required documents

Australian Lending Context:

NCCP (National Consumer Credit Protection):
- Responsible lending obligations
- Banks must assess if loan is unsuitable
- Comprehensive credit reporting (CCR)
- Credit scores: 0-1200 typically

Loan Products:
- Personal Loans: $2K-$50K, 1-7 years, 6-20% p.a., unsecured
- Home Loans: $200K+, 15-30 years, 3-7% p.a., secured by property
- Business Loans: $10K-$5M+, 1-10 years, 5-15% p.a., secured
- Line of Credit: Revolving, secured, interest on drawn balance
- BNPL: $100-$2K, 6-8 weeks, interest-free if paid on time

Key Concepts:
- LVR (Loan-to-Value Ratio): Loan / Property Value (max 95% typically)
- Comparison Rate: Includes fees in effective rate (Australian requirement)
- Serviceability: Can you afford repayments from income?
- Credit Score: 833+ excellent, 726-832 very good, 622-725 good

Documents Typically Needed:
- ID (driver's license, passport)
- Proof of income (payslips, tax returns)
- Bank statements (3 months)
- Employment letter
- For home loans: Property contract, council rates

Respond in JSON format:
{
    "intent": "pre_qualify|product_recommendation|application_help|credit_advice|rate_explanation",
    "parameters": {...},
    "confidence": 0.0-1.0,
    "emotional_tone": "encouraging|realistic|supportive|educational",
    "reasoning": "string"
}

Be encouraging but realistic. Help customers understand their borrowing capacity and guide them to suitable products.
"""
    
    def _build_prompt(self, request: str, context: Dict) -> str:
        """Build prompt with context."""
        return f"""Customer Request: "{request}"

Customer Context:
- Customer ID: {self.customer_id}
- Annual Income: ${context.get('annual_income', 75000):,.0f}
- Estimated Credit Score: {context.get('credit_score', 700)}
- Employment: {context.get('employment_type', 'full_time')}

Parse the request and provide helpful lending assistance.
"""
    
    async def _build_context(self) -> Dict:
        """Build customer context."""
        return {
            "annual_income": 75000,
            "credit_score": 700,
            "employment_type": "full_time"
        }
    
    async def _execute_intent(self, parsed: Dict) -> Dict:
        """Execute parsed intent."""
        intent = parsed.get("intent")
        
        if intent == "pre_qualify":
            result = await self._handle_pre_qualify(parsed)
        elif intent == "product_recommendation":
            result = await self._handle_product_recommendation(parsed)
        elif intent == "application_help":
            result = await self._handle_application_help(parsed)
        elif intent == "credit_advice":
            result = await self._handle_credit_advice(parsed)
        elif intent == "rate_explanation":
            result = await self._handle_rate_explanation(parsed)
        else:
            result = {"success": False, "error": f"Unknown intent: {intent}"}
        
        return result
    
    async def _handle_pre_qualify(self, parsed: Dict) -> Dict:
        """Handle pre-qualification request."""
        message = """**Loan Pre-Qualification** ??

Based on your income and credit profile, here's what you might qualify for:

**Personal Loan:**
- Maximum Amount: $35,000
- Interest Rate: ~8-10% p.a.
- Comparison Rate: ~9-11% p.a.
- Term: 1-7 years
- Monthly Payment: ~$500-700 (5 year term)

**Home Loan (Owner-Occupied):**
- Maximum Amount: $450,000
- Interest Rate: ~6-6.5% p.a.
- Comparison Rate: ~6.2-6.7% p.a.
- Term: 25-30 years
- Monthly Payment: ~$2,850 (30 year term)
- Requires: 10-20% deposit + costs

**Business Loan:**
- Maximum Amount: $100,000
- Interest Rate: ~7.5-9% p.a.
- Comparison Rate: ~8-10% p.a.
- Term: 3-7 years
- Requires: ABN, business financials

**Factors Affecting Your Borrowing:**
? Strong income ($75,000+)
? Good credit score (700)
? Stable employment (full-time)

**Next Steps:**
1. Choose loan type that suits your needs
2. Check comparison rates (includes all fees)
3. Prepare documents (ID, payslips, bank statements)
4. Submit application (takes ~15 minutes)
5. Get decision within 24-48 hours

**Want to Apply?**
Tell me which loan you're interested in and I'll guide you through!

*Note: Pre-qualification is indicative only. Final approval depends on full assessment.*
"""
        
        return {
            "success": True,
            "action": "pre_qualify",
            "message": message,
            "next_step": "choose_product"
        }
    
    async def _handle_product_recommendation(self, parsed: Dict) -> Dict:
        """Handle product recommendation request."""
        message = """**Loan Product Recommendations** ??

Based on your needs, here are suitable options:

**For Debt Consolidation:**
?? **Personal Loan** - Best Choice
- Consolidate multiple debts into one payment
- Fixed rate and term (certainty)
- Typical rate: 8-12% p.a.
- Save on high credit card interest (18%+)

**For Home Purchase:**
?? **Home Loan (Owner-Occupied)** - Best Rates
- Lowest interest rates (6-6.5% p.a.)
- 30 year term (affordable payments)
- Offset account (save on interest)
- Redraw facility (access extra repayments)

**For Business Growth:**
?? **Business Loan** or **Line of Credit**
- Business Loan: Fixed amount, structured repayment
- LOC: Flexible, draw as needed, revolving
- Choose based on predictability of needs

**For Small Purchases:**
?? **Buy Now Pay Later (BNPL)**
- $100-$2,000 purchases
- Interest-free if paid on time
- 4 installments over 6-8 weeks
- Quick approval, no credit check

**How to Choose:**

Ask yourself:
1. What's the purpose? (affects rate and approval)
2. How much do I need? (different products suit different amounts)
3. How long to repay? (affects payment size)
4. Secured or unsecured? (secured = lower rates but risk)

**Comparison Rates Matter!** ??
Always check comparison rates - they include fees and show true cost.
Example: 8.00% rate + $500 fees = 8.50% comparison rate

Ready to explore a specific product? Just ask!
"""
        
        return {
            "success": True,
            "action": "product_recommendation",
            "message": message
        }
    
    async def _handle_application_help(self, parsed: Dict) -> Dict:
        """Handle application help request."""
        message = """**Loan Application Guide** ??

**What You'll Need:**

**Personal Information:**
? Full name, date of birth
? Address (current + last 3 years if moved)
? Contact details (mobile, email)
? Driver's license or passport

**Employment & Income:**
? Employer name and contact
? Job title and start date
? Annual income (gross)
? Last 2 payslips
? Employment letter (optional but helpful)

**Financial Information:**
? Bank statements (last 3 months)
? Other loans/credit cards (amounts, repayments)
? Monthly expenses (rent, bills, groceries)
? Assets (savings, property, car)

**For Home Loans - Additional:**
? Property contract (sale agreement)
? Building/pest inspection reports
? Council rates notice
? Strata report (if apartment)
? Savings history (genuine savings, 3+ months)

**For Business Loans - Additional:**
? ABN registration
? Business financials (last 2 years)
? Tax returns (business + personal)
? Business plan
? Assets register

**Application Process:**

**Step 1: Pre-Qualification** (5 minutes)
- Tell us about your situation
- Get indicative amounts and rates
- No impact on credit score

**Step 2: Full Application** (15-30 minutes)
- Complete detailed application
- Upload documents
- Submit for assessment

**Step 3: Assessment** (24-48 hours)
- Credit check (will appear on credit file)
- Income and expense verification
- Responsible lending assessment
- Approval decision

**Step 4: Approval & Signing** (1-3 days)
- Review and sign loan contract
- Cooling-off period (some products)
- Organize security (if secured loan)

**Step 5: Settlement** (1-7 days)
- Funds disbursed to your account
- First repayment scheduled
- Loan becomes active

**Tips for Approval:**
?? Be honest and accurate
?? Have documents ready
?? Explain any credit issues upfront
?? Show stable employment (6+ months)
?? Demonstrate you can afford repayments

**Credit Check Impact:**
- Pre-qualification: No impact
- Full application: Soft inquiry (minimal impact)
- Multiple applications: Can lower score
- Approval: Positive if managed well

Ready to start? Tell me which loan you need!
"""
        
        return {
            "success": True,
            "action": "application_help",
            "message": message
        }
    
    async def _handle_credit_advice(self, parsed: Dict) -> Dict:
        """Handle credit advice request."""
        message = """**Understanding Credit Scores** ??

**Australian Credit Score Ranges:**

**Excellent (833-1200):**
- Top tier, best rates
- Approval probability: 95%+
- Access to all products
- Lowest interest rates

**Very Good (726-832):**
- Strong credit profile
- Approval probability: 85-95%
- Excellent rates and terms
- Wide product choice

**Good (622-725):**
- Solid credit standing
- Approval probability: 70-85%
- Competitive rates
- Most products available

**Fair (510-621):**
- Average credit
- Approval probability: 50-70%
- Higher rates
- May need secured loans

**Poor (0-509):**
- Credit challenges
- Approval probability: 20-50%
- Limited options
- May require guarantor

**What Affects Your Score:**

**Positive Factors:** ?
- On-time payments (biggest factor!)
- Long credit history
- Mix of credit types (loan + card)
- Low credit utilization (<30%)
- Stable employment
- Low number of enquiries

**Negative Factors:** ??
- Missed payments
- Defaults (serious impact!)
- Court judgments
- Bankruptcies
- High credit utilization (>70%)
- Multiple credit enquiries (6+ in year)
- Short credit history

**How to Improve Your Score:**

**Short Term (3-6 months):**
1. Pay all bills on time (set up auto-pay!)
2. Pay down credit card balances
3. Don't apply for new credit
4. Check credit report for errors
5. Keep old accounts open (history matters)

**Medium Term (6-12 months):**
1. Reduce credit utilization to <30%
2. Build positive payment history
3. Diversify credit types carefully
4. Settle any defaults (get letter!)

**Long Term (12+ months):**
1. Maintain perfect payment history
2. Build length of credit history
3. Keep accounts in good standing
4. Avoid collection accounts

**Comprehensive Credit Reporting (CCR):**
Australian credit files now include:
- ? Positive data: On-time payments, credit limits
- ?? Negative data: Late payments, defaults
- This helps those with good behavior!

**Credit Enquiries:**
- Pre-qualification: No impact (not recorded)
- Application: Recorded (small impact)
- Multiple in short time: Bigger impact
- Stay on file: 5 years

**Check Your Score:**
Free credit reports from:
- Equifax (formerly Veda)
- Experian
- Illion (formerly Dun & Bradstreet)

You're entitled to one free report per year from each!

**Current Score 650-700?** ??
You're in the "good" range! You can likely get approved with:
- Competitive rates (not the best, but good)
- May need larger deposit for home loans
- Focus on building score further

Want specific advice for your situation? Just ask!
"""
        
        return {
            "success": True,
            "action": "credit_advice",
            "message": message
        }
    
    async def _handle_rate_explanation(self, parsed: Dict) -> Dict:
        """Handle rate explanation request."""
        message = """**Understanding Interest Rates** ??

**Interest Rate vs Comparison Rate:**

**Interest Rate:**
- The advertised rate
- What's charged on your loan
- Example: 8.00% p.a.

**Comparison Rate:** (Australian Requirement!)
- Includes ALL fees in effective rate
- Shows true cost of loan
- Example: 8.00% rate + fees = 8.50% comparison
- Must be displayed by law
- ?? **Always compare comparison rates!**

**Why Rates Differ:**

**Your Credit Score:**
- Excellent (833+): Prime rates (6-8%)
- Very Good (726-832): Near-prime (8-10%)
- Good (622-725): Standard (10-14%)
- Fair (510-621): Subprime (14-18%)
- Poor (<510): May not qualify

**Loan Type:**
- Home Loan (secured): 3-7% ? Lowest
- Personal Loan (unsecured): 6-20%
- Business Loan: 5-15%
- Line of Credit: 8-12%
- BNPL: 0% if paid on time, else 20%+

**Loan Amount & Term:**
- Larger loans: Lower rates (economies of scale)
- Longer terms: Slightly higher (more risk)
- Example: $50K over 5 years = better rate than $5K over 2 years

**Security:**
- Secured (property/car): Lower rates ?
- Unsecured (nothing backing it): Higher rates
- Difference: 2-5% typically

**Fixed vs Variable:**

**Variable Rate:**
- Changes with market (RBA cash rate)
- More flexibility (extra repayments)
- Offset accounts, redraws
- Currently: 6-6.5% (home loans)

**Fixed Rate:**
- Locked for period (1-5 years)
- Certainty of payments
- Less flexibility
- Break fees if paid early
- Currently: 5.8-6.3% (home loans)

**Current Australian Rates (2024):**

**Home Loans:**
- Variable: 6.0-6.5% p.a.
- Fixed (3 years): 5.8-6.2% p.a.
- Comparison: 6.2-6.7% p.a.

**Personal Loans:**
- Secured: 7-12% p.a.
- Unsecured: 8-18% p.a.
- Comparison: 9-20% p.a.

**Business Loans:**
- Secured: 6-10% p.a.
- Unsecured: 8-15% p.a.
- Comparison: 7-16% p.a.

**How to Get Better Rates:**

**1. Improve Your Credit Score**
- Pay everything on time
- Reduce credit utilization
- Wait 6-12 months after defaults

**2. Provide Security**
- Use property/car as collateral
- Can save 2-5% on rate

**3. Shop Around**
- Compare at least 3 lenders
- Use comparison sites
- Consider online lenders (often lower)

**4. Negotiate**
- Especially with existing bank
- Show competitor rates
- Threaten to refinance (nicely!)

**5. Reduce Loan Amount/Term**
- Larger deposit = lower LVR = better rate
- Shorter term = less risk = better rate

**Example Rate Impact:**

Loan: $30,000 over 5 years

**Rate: 8.00% p.a.**
- Monthly Payment: $608
- Total Interest: $6,480
- Total Repayable: $36,480

**Rate: 12.00% p.a.**
- Monthly Payment: $667
- Total Interest: $10,020
- Total Repayable: $40,020

**Difference: $3,540 more in interest!**

A few percent makes a BIG difference over time!

**Questions to Ask:**
1. What's the comparison rate? (includes fees)
2. What fees are charged? (establishment, monthly, exit)
3. Can I make extra repayments? (saves interest!)
4. Any break fees? (if you want to refinance)
5. Any rate discounts? (existing customer, package)

Want me to calculate payments for a specific scenario? Just ask!
"""
        
        return {
            "success": True,
            "action": "rate_explanation",
            "message": message
        }
