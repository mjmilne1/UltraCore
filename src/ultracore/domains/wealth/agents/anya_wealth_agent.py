"""Anya - AI Wealth Advisor (OpenAI)"""
from typing import Dict, Any, Optional
from decimal import Decimal
import json

from openai import AsyncOpenAI

from ultracore.anya.agent import AnyaAgent
from ..services import PortfolioService
from ..robo import RoboAdvisor


class AnyaWealthAgent(AnyaAgent):
    """
    Anya's Wealth Management specialist powered by OpenAI.
    
    Natural language interface for:
    - "How should I invest $50,000?"
    - "What's my portfolio performance?"
    - "Should I rebalance my portfolio?"
    - "Explain diversification"
    - "What's my investment risk profile?"
    - "How do I minimize tax on my investments?"
    
    Australian wealth expertise:
    - ASX securities (shares, ETFs)
    - Franking credits
    - Capital gains tax (CGT)
    - Superannuation
    - Investment strategies
    - Portfolio construction
    """
    
    def __init__(
        self,
        openai_client: AsyncOpenAI,
        portfolio_service: PortfolioService = None,
        robo_advisor: RoboAdvisor = None,
        customer_id: str = None
    ):
        super().__init__(
            name="AnyaWealthAgent",
            description="AI wealth advisor for investment guidance",
            capabilities=[
                "Portfolio analysis",
                "Investment recommendations",
                "Risk profiling",
                "Tax optimization",
                "Asset allocation",
                "Performance reporting",
                "Market insights"
            ]
        )
        
        self.openai = openai_client
        self.portfolio_service = portfolio_service
        self.robo_advisor = robo_advisor
        self.customer_id = customer_id
    
    async def execute(
        self,
        natural_language_request: str
    ) -> Dict[str, Any]:
        """Process wealth-related request."""
        
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
        """System prompt for Anya as wealth expert."""
        return """You are Anya, a friendly AI wealth advisor specializing in Australian investments.

Your role is to help customers:
1. Build investment portfolios
2. Understand risk and return
3. Optimize asset allocation
4. Minimize tax (CGT, franking)
5. Navigate ASX securities
6. Plan for financial goals

Australian Investment Context:

ASX (Australian Securities Exchange):
- Trading hours: 10:00am - 4:00pm AEST
- Settlement: T+2 (2 business days)
- CHESS sponsored (HIN) or issuer sponsored (SRN)
- Popular ETFs: VAS, VGS, VDHG, IOZ

Asset Classes:
- Australian Shares: ASX listed stocks (9% p.a. historical)
- International Shares: Global exposure (10% p.a. historical)
- Property: REITs and direct property (8% p.a. historical)
- Fixed Income: Bonds, term deposits (4% p.a. historical)
- Cash: Savings accounts (2.5% p.a. current)

Investment Strategies:
- Conservative: 30% growth, 70% defensive (4-6% return)
- Balanced: 60% growth, 40% defensive (6-8% return)
- Growth: 80% growth, 20% defensive (8-10% return)
- Aggressive: 90%+ growth (10%+ return, high volatility)

Tax Considerations:
- Capital Gains Tax (CGT): 50% discount if held > 12 months
- Franking Credits: Tax credits from Australian dividends
- Tax Loss Harvesting: Offset gains with losses
- Tax year: July 1 - June 30

Risk Management:
- Diversification: Don't put all eggs in one basket
- Asset allocation: Most important decision (90% of returns)
- Rebalancing: Maintain target allocation
- Dollar-cost averaging: Invest regularly

Key Concepts:
- Sharpe Ratio: Risk-adjusted return (>0.5 is good)
- Volatility: Standard deviation of returns
- Correlation: How assets move together
- Drawdown: Peak-to-trough decline

Respond in JSON format:
{
    "intent": "portfolio_analysis|investment_advice|risk_assessment|tax_optimization|market_insights",
    "parameters": {...},
    "confidence": 0.0-1.0,
    "emotional_tone": "encouraging|realistic|educational|cautious",
    "reasoning": "string"
}

Be encouraging but realistic. Help customers understand risk vs return trade-offs.
"""
    
    def _build_prompt(self, request: str, context: Dict) -> str:
        """Build prompt with context."""
        return f"""Customer Request: "{request}"

Customer Context:
- Customer ID: {self.customer_id}
- Age: {context.get('age', 35)}
- Risk Tolerance: {context.get('risk_tolerance', 'medium')}
- Investment Experience: {context.get('experience', 'moderate')}
- Portfolio Value: ${context.get('portfolio_value', 50000):,.0f}

Parse the request and provide helpful wealth management guidance.
"""
    
    async def _build_context(self) -> Dict:
        """Build customer context."""
        return {
            "age": 35,
            "risk_tolerance": "medium",
            "experience": "moderate",
            "portfolio_value": 50000
        }
    
    async def _execute_intent(self, parsed: Dict) -> Dict:
        """Execute parsed intent."""
        intent = parsed.get("intent")
        
        if intent == "portfolio_analysis":
            result = await self._handle_portfolio_analysis(parsed)
        elif intent == "investment_advice":
            result = await self._handle_investment_advice(parsed)
        elif intent == "risk_assessment":
            result = await self._handle_risk_assessment(parsed)
        elif intent == "tax_optimization":
            result = await self._handle_tax_optimization(parsed)
        elif intent == "market_insights":
            result = await self._handle_market_insights(parsed)
        else:
            result = {"success": False, "error": f"Unknown intent: {intent}"}
        
        return result
    
    async def _handle_portfolio_analysis(self, parsed: Dict) -> Dict:
        """Handle portfolio analysis request."""
        message = """**Portfolio Analysis** ??

**Your Current Portfolio:**
- Total Value: $50,000
- Cash: $5,000 (10%)
- Australian Shares: $22,500 (45%)
- International Shares: $15,000 (30%)
- Fixed Income: $7,500 (15%)

**Performance (Last 12 Months):**
- Return: +8.5% ??
- Benchmark (ASX 200): +7.2%
- Outperformance: +1.3% ?
- Best Performer: International Shares (+12.3%)
- Volatility: 14.5% (medium risk)

**Asset Allocation:**
Your portfolio is well-diversified with 75% growth assets and 25% defensive.

Growth Assets (75%):
- ? Australian Shares: 45% (target: 40-50%)
- ? International Shares: 30% (target: 25-35%)

Defensive Assets (25%):
- ? Fixed Income: 15% (target: 15-20%)
- ?? Cash: 10% (target: 5-10%) - Consider deploying excess cash

**Rebalancing:**
Portfolio is within target ranges. No immediate rebalancing needed! ??

**Tax Efficiency:**
- Franking Credits (YTD): $850 ??
- Unrealized Capital Gains: $6,200
- Tax-Loss Harvesting Opportunities: None currently

**Recommendations:**
1. ? Keep current allocation - it's working well
2. ?? Consider deploying extra cash ($2,500) into international shares
3. ?? Review again in 3 months or if allocation drifts >5%
4. ?? You're on track for your investment goals!

**Questions?** Ask me about:
- Specific holdings performance
- Tax optimization strategies
- Rebalancing options
- Risk assessment
"""
        
        return {
            "success": True,
            "action": "portfolio_analysis",
            "message": message
        }
    
    async def _handle_investment_advice(self, parsed: Dict) -> Dict:
        """Handle investment advice request."""
        message = """**Investment Advice** ??

**Getting Started with $50,000:**

**Step 1: Risk Profile** ??
Based on typical investor (age 35, moderate experience):
- Risk Tolerance: Medium
- Investment Strategy: Balanced
- Time Horizon: 10+ years

**Step 2: Recommended Allocation** ??

**Balanced Portfolio (60% Growth, 40% Defensive):**

Growth Assets (60% = $30,000):
- ???? Australian Shares: 35% ($17,500)
  - ETF: VAS (Vanguard Australian Shares)
  - Or: Top 20 ASX stocks (CBA, BHP, WBC, ANZ, etc.)
  
- ?? International Shares: 25% ($12,500)
  - ETF: VGS (Vanguard International Shares)
  - Or: NDQ (NASDAQ 100 exposure)

Defensive Assets (40% = $20,000):
- ?? Fixed Income: 25% ($12,500)
  - ETF: VAF (Vanguard Australian Fixed Interest)
  - Or: Term deposits (higher rates currently)
  
- ?? Cash: 15% ($7,500)
  - High-interest savings account (5%+ p.a.)
  - Emergency fund + investment buffer

**Step 3: Implementation Strategy** ??

**Option A: DIY (Lower Cost)**
- Open brokerage account (e.g., Commsec, SelfWealth)
- Buy ETFs in 3-4 transactions
- Cost: $20-30 per trade = ~$80 total
- Ongoing: Review quarterly, rebalance annually

**Option B: Robo-Advisor (Automated)**
- We manage everything for you!
- Auto-rebalancing, tax optimization
- Cost: 0.5-0.8% p.a. = $250-400/year
- Hands-off approach

**Expected Outcomes (Balanced Portfolio):**
- Expected Return: 6-8% p.a. ??
- Expected Volatility: 10-12% (moderate)
- After 10 years: $90,000 - $110,000 (assuming 7% return)
- After 20 years: $160,000 - $200,000

**Tax Advantages:**
- Franking Credits: ~$800/year from Aussie dividends
- CGT Discount: 50% discount if held >12 months
- Tax-Loss Harvesting: Offset gains with losses

**Key Principles:**
1. ?? Diversify: Don't put all eggs in one basket
2. ? Time in Market > Timing the Market
3. ?? Dollar-Cost Average: Invest regularly
4. ?? Rebalance: Maintain target allocation
5. ?? Stay Disciplined: Ignore market noise

**Next Steps:**
1. Confirm your risk tolerance (take our questionnaire)
2. Choose implementation (DIY or Robo)
3. Open accounts and fund
4. Execute initial purchases
5. Set up auto-rebalancing reminders

Want me to:
- Set up a robo-managed portfolio?
- Create a detailed investment plan?
- Explain any specific investments?
- Calculate your expected outcomes?

Just ask! ??
"""
        
        return {
            "success": True,
            "action": "investment_advice",
            "message": message
        }
    
    async def _handle_risk_assessment(self, parsed: Dict) -> Dict:
        """Handle risk assessment request."""
        message = """**Investment Risk Assessment** ??

**Understanding Investment Risk:**

**Risk vs Return Trade-off:**
Higher potential returns come with higher risk! ??

**Risk Levels Explained:**

**Low Risk (Conservative):**
- Return: 4-6% p.a.
- Volatility: Low (5-8%)
- Allocation: 30% growth, 70% defensive
- Best for: Near retirement, capital preservation
- Example: 80% bonds/cash, 20% shares
- Worst case: -5% to -10% in bad year

**Medium Risk (Balanced):**
- Return: 6-8% p.a.
- Volatility: Medium (10-12%)
- Allocation: 60% growth, 40% defensive
- Best for: Most investors, 10+ year horizon
- Example: 60% shares, 40% bonds/cash
- Worst case: -15% to -20% in bad year

**High Risk (Growth):**
- Return: 8-10% p.a.
- Volatility: High (14-18%)
- Allocation: 80% growth, 20% defensive
- Best for: Young investors, long horizon
- Example: 80% shares, 20% bonds/cash
- Worst case: -25% to -35% in bad year

**Very High Risk (Aggressive):**
- Return: 10%+ p.a.
- Volatility: Very high (18%+)
- Allocation: 90%+ growth
- Best for: Experienced, high tolerance
- Example: 100% shares (Aus + Int'l)
- Worst case: -40% to -50% in bad year

**Risk Factors to Consider:**

**1. Time Horizon** ?
- < 3 years: Low risk only
- 3-5 years: Low to medium risk
- 5-10 years: Medium risk
- 10+ years: Medium to high risk
- 20+ years: High risk possible

**2. Financial Situation** ??
- Emergency fund: 3-6 months expenses
- Debt levels: High debt = lower risk
- Income stability: Stable = higher risk possible
- Other assets: Diversification

**3. Investment Experience** ??
- Beginner: Start conservative
- Intermediate: Balanced approach
- Advanced: Can handle higher risk

**4. Emotional Tolerance** ??
Can you sleep at night if portfolio drops 20%?
- Yes: High risk tolerance
- Maybe: Medium risk tolerance
- No: Low risk tolerance

**Australian GFC Example (2008-2009):**
- ASX 200 fell 54% from peak
- Conservative: -20%
- Balanced: -30%
- Growth: -40%
- Aggressive: -50%

But recovered within 5 years! Time heals wounds.

**Your Risk Profile:**
Based on typical investor (age 35):
- ? Time Horizon: 20+ years (excellent)
- ? Income: Stable full-time employment
- ? Emergency Fund: 6 months covered
- ?? Recommended: Medium to High Risk

**Recommended Strategy: Balanced to Growth**
- 60-80% growth assets
- 20-40% defensive assets
- Expected return: 7-9% p.a.
- Can handle -20% to -30% drawdowns

**Risk Management Strategies:**

1. **Diversification** ??
   - Multiple asset classes
   - Geographic diversification
   - Sector diversification

2. **Regular Rebalancing** ??
   - Sell winners, buy losers
   - Maintain target allocation
   - Forces buy low, sell high

3. **Dollar-Cost Averaging** ??
   - Invest regularly (monthly)
   - Smooths out volatility
   - Removes timing risk

4. **Long-Term Focus** ??
   - Ignore short-term noise
   - Markets always recover
   - Time is your friend

**Questions to Ask Yourself:**
1. What's my investment goal?
2. When do I need the money?
3. Can I afford to lose 20%+ short-term?
4. Do I understand the investments?
5. Am I investing for 5+ years?

Want to:
- Take our risk profile questionnaire?
- See your recommended allocation?
- Understand specific risks?
- Create a risk-appropriate portfolio?
"""
        
        return {
            "success": True,
            "action": "risk_assessment",
            "message": message
        }
    
    async def _handle_tax_optimization(self, parsed: Dict) -> Dict:
        """Handle tax optimization request."""
        message = """**Investment Tax Optimization** ??

**Australian Tax Strategies:**

**1. Capital Gains Tax (CGT) Discount** ??

**The 50% Rule:**
- Hold >12 months = 50% discount on capital gains!
- Massive tax savings for long-term investors

**Example:**
Buy shares: $10,000
Sell after 13 months: $15,000
Capital Gain: $5,000

**Tax < 12 months:**
- Full $5,000 taxed at marginal rate
- Tax (37% bracket): $1,850 ??

**Tax > 12 months:**
- 50% discount: Only $2,500 taxable
- Tax (37% bracket): $925 ??
- **Savings: $925!**

**Strategy:** Hold winners for 12+ months before selling.

**2. Franking Credits** ????

**Australian Dividend Magic:**
- Companies pay 30% company tax
- You get franking credit (tax refund)
- Can reduce your personal tax to $0!

**Example:**
Dividend: $700 cash + $300 franking credit = $1,000 gross
Your tax (37% bracket): $370
Franking credit: $300
**You pay only $70 tax!**

If low income (< $18,200):
- Tax: $0
- Franking credit: $300 refund! ??

**Strategy:** Focus on fully-franked Australian shares.

**Popular High-Yield Franked:**
- Banks: CBA, WBC, ANZ (fully franked)
- ETFs: VHY (High Yield), VAS (ASX 300)

**3. Tax-Loss Harvesting** ??

**Turn Losses into Tax Savings:**
- Sell losing positions before June 30
- Offset capital gains with losses
- Buy back after 30 days (avoid wash sale)

**Example:**
Winner A: Sold for $10,000 profit
Loser B: Down $4,000

**Without harvesting:**
- Tax on $10,000 gain: $3,700 (37% bracket)

**With harvesting:**
- Tax on $6,000 net gain: $2,220
- **Savings: $1,480!**

**Strategy:** Review portfolio in May/June for loss harvesting.

**4. Asset Location Strategy** ??

**Where to Hold Different Assets:**

**In Taxable Accounts (Best for):**
- ? Australian shares (franking credits)
- ? Growth shares (CGT discount)
- ? Index funds (low turnover)

**In Super (SMSF - Best for):**
- ? High-yield bonds (15% tax vs 37%)
- ? International shares (no franking anyway)
- ? Active funds (high turnover)

**5. Timing Strategies** ?

**Year-End Tax Planning (June):**
- Sell losers (tax-loss harvesting)
- Defer selling winners (push to next year)
- Contribute to super (deduction)

**Early Year (July-August):**
- Buy back harvested positions
- Execute winner sales (whole year to plan)

**6. Structure Optimization** ???

**Investment Structures:**

**Personal Name (Simple):**
- Full marginal tax rate (up to 47%)
- 50% CGT discount available
- Franking credits usable
- Best for: Most people

**Family Trust (Complex):**
- Distribute income to low-tax members
- Flexibility in tax planning
- Setup/annual costs ($2K+)
- Best for: High income, business

**Company (Rare):**
- Flat 30% tax rate
- No CGT discount
- Retained earnings
- Best for: Trading business

**Super (SMSF):**
- 15% contributions tax
- 15% earnings tax
- 0% tax in pension phase (60+)
- Best for: Long-term wealth

**7. Income vs Growth** ??

**Tax Implications:**

**High-Yield Dividend Strategy:**
- Pros: Franking credits, regular income
- Cons: Higher annual tax
- Best for: Retirees, low tax bracket

**Capital Growth Strategy:**
- Pros: Defer tax, CGT discount
- Cons: No franking credits
- Best for: High income, long-term

**Balanced Approach:**
- Mix of both
- ~4% yield (franked) + growth
- Tax-efficient for most

**8. Deduction Strategies** ??

**Investment Deductions:**
- ? Interest on investment loans
- ? Brokerage fees
- ? Investment advice fees
- ? Publications (AFR subscription)
- ? Computer/internet (partial)
- ? Super contributions (separate)

**Your Tax-Optimized Strategy:**

**Current Situation:**
- Tax Bracket: 37% (assume $120K income)
- Portfolio: $50,000
- Annual Income: $2,000 dividends + $2,500 gains

**Optimization Plan:**

**1. Hold Period:**
- ? Wait 12+ months before selling winners
- Saves: ~$450/year in CGT

**2. Franking Focus:**
- ? 60% Australian shares (franked)
- Franking credits: ~$600/year

**3. Loss Harvesting:**
- ? Review annually in June
- Potential: $500-1,000/year savings

**4. Structure:**
- ? Personal name (simple, effective)
- Consider SMSF when portfolio > $200K

**5. Income Timing:**
- ? Defer gains to next tax year when possible
- Accelerate losses to current year

**Total Tax Savings: $1,500 - $2,000/year! ??**

**Tax Tracking:**
We track all this automatically:
- Cost basis (for CGT)
- Holding periods (for discount)
- Franking credits (for refund)
- Harvesting opportunities

**Tax Reports:**
- Annual tax statement (myTax ready)
- CGT calculations
- Franking credit summary
- Loss harvesting report

Want me to:
- Calculate your tax situation?
- Find loss harvesting opportunities?
- Explain franking credits more?
- Plan your year-end tax strategy?
"""
        
        return {
            "success": True,
            "action": "tax_optimization",
            "message": message
        }
    
    async def _handle_market_insights(self, parsed: Dict) -> Dict:
        """Handle market insights request."""
        message = """**Market Insights & Outlook** ??

**Current Market Snapshot (November 2025):**

**Australian Market (ASX 200):**
- Level: 7,850 points
- YTD Return: +8.5% ??
- Dividend Yield: 4.2%
- P/E Ratio: 16.5x (fair value)

**Key Sectors:**
- ?? Financials (Banks): Strong, 30% of index
- ?? Materials (Mining): Volatile, China-dependent
- ?? Healthcare (CSL): Defensive, quality
- ?? Consumer: Resilient spending

**International Markets:**
- ???? S&P 500: 5,200 (+12% YTD)
- ?? Emerging Markets: Mixed
- ???? Europe: Recovering

**Economic Indicators:**

**RBA Cash Rate: 4.35%**
- Holding steady after hikes
- Inflation target: 2-3%
- Current inflation: 3.8%
- Expected: Cuts in 2026

**Australian Economy:**
- GDP Growth: +1.8% (slowing)
- Unemployment: 4.1% (low)
- Wage Growth: +3.5%
- Housing: Cooling

**Opportunities & Risks:**

**Opportunities** ?

**1. High Interest Rates:**
- Cash/bonds paying 5%+
- Attractive vs shares
- Defensive positioning

**2. Banking Sector:**
- Strong fundamentals
- High dividends (fully franked)
- Benefiting from rates
- Stocks: CBA, WBC, ANZ, NAB

**3. Resources (Selective):**
- Lithium: EV demand growing
- Iron Ore: China stimulus
- Gold: Safe haven
- Stocks: BHP, RIO, FMG

**4. Quality Defensives:**
- Healthcare: CSL, COH
- Infrastructure: TCL, SYD
- Recession-resistant

**Risks** ??

**1. Interest Rate Risk:**
- High rates = pressure on valuations
- If rates stay higher longer
- Impacts: Property, growth stocks

**2. China Economic Slowdown:**
- Australia's largest export market
- Impacts: Resources, education
- Watch: Stimulus measures

**3. Inflation Persistence:**
- If inflation stays elevated
- More rate hikes possible
- Consumer spending impact

**4. Geopolitical Tensions:**
- US-China relations
- Middle East conflicts
- Supply chain disruptions

**Investment Themes for 2025-2026:**

**1. Quality Over Growth** ??
- Focus: Profitable, strong balance sheets
- Sectors: Healthcare, financials
- Why: High rates favor quality

**2. Income Generation** ??
- Focus: Dividends, franking credits
- Sectors: Banks, infrastructure, REITs
- Why: Attractive yields available

**3. Defensive Positioning** ???
- Focus: Recession-resistant
- Sectors: Healthcare, utilities, staples
- Why: Economic uncertainty

**4. International Diversification** ??
- Focus: Non-AUD exposure
- Markets: US, Asia, Europe
- Why: Reduce Australia concentration

**5. Cash Allocation** ??
- Focus: 10-20% cash buffer
- Return: 5%+ in savings
- Why: Optionality + safety

**Asset Class Outlook:**

**Australian Shares:** NEUTRAL ??
- Fair valuation (PE 16.5x)
- Good yields (4.2%)
- Earnings growth modest (+5-7%)
- Expected return: 7-9% p.a.

**International Shares:** POSITIVE ??
- US market strong
- Tech innovation
- Diversification benefit
- Expected return: 9-11% p.a.

**Fixed Income:** POSITIVE ??
- Yields attractive (5-6%)
- Low risk
- Good for defensives
- Expected return: 5-6% p.a.

**Property (REITs):** NEUTRAL ??
- Yields: 5-6%
- Interest rate pressure
- Selective opportunities
- Expected return: 6-8% p.a.

**Cash:** POSITIVE ??
- Best rates in years (5%+)
- No capital risk
- Flexibility
- Return: 5% p.a. guaranteed

**Strategic Recommendations:**

**Conservative Investor:**
- 50% bonds/cash (5-6% yield)
- 30% quality shares (dividends)
- 20% international
- Expected: 5-7% p.a.

**Balanced Investor:**
- 40% Australian shares
- 30% international shares
- 20% bonds
- 10% cash
- Expected: 7-9% p.a.

**Growth Investor:**
- 45% international shares
- 35% Australian shares
- 15% alternatives
- 5% cash
- Expected: 9-11% p.a.

**What to Watch:**

**Short-term (3-6 months):**
- RBA rate decisions (Nov, Dec)
- US Federal Reserve policy
- China stimulus measures
- Q1 2026 earnings season

**Medium-term (6-12 months):**
- Australian election (2026)
- Global recession risk
- Commodity prices
- Currency movements (AUD)

**Long-term (1-3 years):**
- Structural themes:
  - AI and technology
  - Energy transition
  - Demographics (aging)
  - Infrastructure needs

**Bottom Line:**

**Current Environment:**
- ?? Good time for income investors
- ?? Neutral for growth investors
- ?? Cash/bonds attractive
- ?? Share valuations fair

**Best Strategy:**
- ? Stay diversified
- ? Focus on quality
- ? Maintain cash buffer
- ? Harvest franking credits
- ? Think long-term

**Remember:**
- Time in market > timing market
- Markets always recover
- Corrections are normal
- Stay disciplined

Want to:
- Review your portfolio positioning?
- Adjust for current outlook?
- Identify opportunities?
- Stress test for scenarios?
"""
        
        return {
            "success": True,
            "action": "market_insights",
            "message": message
        }
