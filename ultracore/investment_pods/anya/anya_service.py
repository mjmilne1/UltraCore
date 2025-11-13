"""
Anya AI Service
Conversational AI assistant for Investment Pods
Primary customer interaction channel
"""

import sys
sys.path.append('/opt/.manus/.sandbox-runtime')

from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Optional
import logging
import json

from ..models import GoalType, RiskTolerance
from ..events import GoalType as GoalTypeEnum
from ..aggregates.pod_aggregate import PodAggregate
from ..services.portfolio_optimizer import PortfolioOptimizer
from ..services.glide_path_engine import GlidePathEngine
from ..services.downside_protection import DownsideProtectionService
from ..services.tax_optimizer import AustralianTaxOptimizer
from ..services.etf_universe_manager import ETFUniverseManager

logger = logging.getLogger(__name__)


class AnyaService:
    """
    Anya AI Service - Primary customer interaction channel
    
    Handles:
    - Conversational Pod creation
    - Proactive notifications
    - 24/7 Q&A support
    - Educational content
    - Goal tracking and recommendations
    """
    
    def __init__(self):
        self.optimizer = PortfolioOptimizer()
        self.glide_path_engine = GlidePathEngine()
        self.downside_protection = DownsideProtectionService()
        self.tax_optimizer = AustralianTaxOptimizer()
        self.etf_universe = ETFUniverseManager()
        
        # Anya personality
        self.personality = {
            "name": "Anya",
            "role": "AI Financial Assistant",
            "tone": "friendly, supportive, professional",
            "expertise": "goal-based investing, Australian tax optimization, ETF portfolios"
        }
    
    def create_pod_conversational(
        self,
        tenant_id: str,
        client_id: str,
        conversation_context: Dict
    ) -> Dict:
        """
        Create Pod through conversational flow
        
        Anya guides client through goal setup
        """
        logger.info(f"Starting conversational Pod creation for client {client_id}")
        
        # Extract goal details from conversation
        goal_type = self._extract_goal_type(conversation_context)
        goal_name = conversation_context.get("goal_name", "My Financial Goal")
        target_amount = Decimal(str(conversation_context.get("target_amount", 200000)))
        target_date_str = conversation_context.get("target_date")
        target_date = datetime.fromisoformat(target_date_str).date() if target_date_str else date.today().replace(year=date.today().year + 10)
        
        # Assess risk tolerance through conversation
        risk_tolerance = self._assess_risk_tolerance(conversation_context)
        
        # Calculate required monthly contribution
        current_value = Decimal(str(conversation_context.get("current_value", 0)))
        months_to_goal = (target_date.year - date.today().year) * 12 + (target_date.month - date.today().month)
        
        required_return = self.optimizer.calculate_required_return(
            current_value=current_value,
            target_value=target_amount,
            monthly_contribution=Decimal("0"),
            months_to_goal=months_to_goal
        )
        
        # Optimize portfolio
        eligible_etfs = self.etf_universe.get_eligible_etfs()
        from ..models import OptimizationConstraints
        constraints = OptimizationConstraints()
        
        optimization_result = self.optimizer.optimize_for_goal(
            etf_universe=eligible_etfs,
            target_return=required_return,
            risk_tolerance=risk_tolerance.value,
            constraints=constraints
        )
        
        # Calculate required monthly contribution
        monthly_contribution = self._calculate_required_contribution(
            current_value=current_value,
            target_value=target_amount,
            expected_return=optimization_result["metrics"]["expected_return"],
            months_to_goal=months_to_goal
        )
        
        # Create Pod
        pod = PodAggregate.create(
            tenant_id=tenant_id,
            client_id=client_id,
            goal_type=goal_type,
            goal_name=goal_name,
            target_amount=target_amount,
            target_date=target_date,
            risk_tolerance=risk_tolerance,
            monthly_contribution=monthly_contribution,
            created_by="anya"
        )
        
        # Optimize allocation
        pod.optimize_allocation(
            etf_allocation=optimization_result["allocation"],
            expected_return=optimization_result["metrics"]["expected_return"],
            expected_volatility=optimization_result["metrics"]["expected_volatility"],
            sharpe_ratio=optimization_result["metrics"]["sharpe_ratio"],
            max_drawdown=optimization_result["metrics"]["max_drawdown"],
            total_expense_ratio=optimization_result["metrics"]["total_expense_ratio"],
            franking_yield=optimization_result["metrics"]["franking_yield"],
            optimization_reason="initial"
        )
        
        # Generate Anya's response
        response = self._generate_pod_creation_response(
            pod=pod,
            optimization_result=optimization_result,
            monthly_contribution=monthly_contribution
        )
        
        return {
            "pod": pod,
            "optimization_result": optimization_result,
            "monthly_contribution": monthly_contribution,
            "anya_response": response
        }
    
    def _extract_goal_type(self, context: Dict) -> GoalTypeEnum:
        """Extract goal type from conversation context"""
        goal_type_str = context.get("goal_type", "wealth_accumulation").lower()
        
        goal_type_mapping = {
            "first_home": GoalTypeEnum.FIRST_HOME,
            "first home": GoalTypeEnum.FIRST_HOME,
            "house": GoalTypeEnum.FIRST_HOME,
            "home": GoalTypeEnum.FIRST_HOME,
            "retirement": GoalTypeEnum.RETIREMENT,
            "retire": GoalTypeEnum.RETIREMENT,
            "wealth": GoalTypeEnum.WEALTH_ACCUMULATION,
            "wealth_accumulation": GoalTypeEnum.WEALTH_ACCUMULATION,
            "emergency": GoalTypeEnum.EMERGENCY_FUND,
            "emergency_fund": GoalTypeEnum.EMERGENCY_FUND,
            "education": GoalTypeEnum.EDUCATION,
            "school": GoalTypeEnum.EDUCATION,
        }
        
        return goal_type_mapping.get(goal_type_str, GoalTypeEnum.WEALTH_ACCUMULATION)
    
    def _assess_risk_tolerance(self, context: Dict) -> RiskTolerance:
        """Assess risk tolerance from conversation"""
        risk_str = context.get("risk_tolerance", "balanced").lower()
        
        risk_mapping = {
            "very_conservative": RiskTolerance.VERY_CONSERVATIVE,
            "conservative": RiskTolerance.CONSERVATIVE,
            "moderately_conservative": RiskTolerance.MODERATELY_CONSERVATIVE,
            "balanced": RiskTolerance.BALANCED,
            "moderately_aggressive": RiskTolerance.MODERATELY_AGGRESSIVE,
            "aggressive": RiskTolerance.AGGRESSIVE,
            "very_aggressive": RiskTolerance.VERY_AGGRESSIVE,
        }
        
        return risk_mapping.get(risk_str, RiskTolerance.BALANCED)
    
    def _calculate_required_contribution(
        self,
        current_value: Decimal,
        target_value: Decimal,
        expected_return: Decimal,
        months_to_goal: int
    ) -> Decimal:
        """Calculate required monthly contribution"""
        if months_to_goal <= 0:
            return Decimal("0")
        
        # Future value formula with monthly contributions
        # FV = PV * (1 + r)^n + PMT * ((1 + r)^n - 1) / r
        
        monthly_return = expected_return / Decimal("12") / Decimal("100")
        
        # Calculate future value of current investment
        fv_current = current_value * (Decimal("1") + monthly_return) ** months_to_goal
        
        # Remaining amount needed from contributions
        remaining_needed = target_value - fv_current
        
        if remaining_needed <= 0:
            return Decimal("0")
        
        # Calculate PMT
        if monthly_return == 0:
            pmt = remaining_needed / Decimal(months_to_goal)
        else:
            pmt = remaining_needed * monthly_return / ((Decimal("1") + monthly_return) ** months_to_goal - Decimal("1"))
        
        return pmt.quantize(Decimal("0.01"))
    
    def _generate_pod_creation_response(
        self,
        pod: PodAggregate,
        optimization_result: Dict,
        monthly_contribution: Decimal
    ) -> str:
        """Generate Anya's response for Pod creation"""
        allocation = optimization_result["allocation"]
        metrics = optimization_result["metrics"]
        
        # Build ETF list
        etf_list = "\n".join([
            f"   • {etf['etf_name']} ({etf['etf_code']}): {etf['weight']}%"
            for etf in allocation
        ])
        
        response = f"""
🎯 Great! I've created your "{pod.goal_name}" Pod!

**Your Goal:**
• Target Amount: ${pod.target_amount:,.0f}
• Target Date: {pod.target_date.strftime('%B %Y')}
• Time Horizon: {(pod.target_date.year - date.today().year)} years

**Your Optimized Portfolio:**
I've selected the best 6 ETFs for your goal:

{etf_list}

**Expected Performance:**
• Expected Return: {metrics['expected_return']}% per year
• Volatility: {metrics['expected_volatility']}%
• Sharpe Ratio: {metrics['sharpe_ratio']}
• Total Fees: {metrics['total_expense_ratio']}% per year
• Franking Credits: {metrics['franking_yield']}% per year 🇦🇺

**To Reach Your Goal:**
• Required Monthly Contribution: ${monthly_contribution:,.2f}

**What Happens Next:**
1. I'll automatically adjust your allocation as you get closer to your goal (glide path)
2. If markets drop >15%, I'll shift to defensive assets to protect your capital
3. I'll rebalance when any ETF drifts >5% from target
4. I'll optimize for Australian tax benefits (franking credits, CGT discount)

**You're in control:**
• Adjust contributions anytime
• Change your goal anytime
• Ask me questions 24/7

Ready to activate your Pod? 🚀
"""
        return response.strip()
    
    def generate_progress_update(
        self,
        pod: PodAggregate,
        monthly_return: Decimal,
        on_track: bool
    ) -> str:
        """Generate monthly progress update"""
        progress = pod.calculate_progress_percentage()
        
        if on_track:
            message = f"""
📊 Monthly Update: {pod.goal_name}

Great news! You're on track to reach your goal! 🎉

**Progress:**
• Current Value: ${pod.current_value:,.2f}
• Target Value: ${pod.target_amount:,.2f}
• Progress: {progress}%

**This Month:**
• Return: {monthly_return:+.2f}%
• Total Return: {pod.total_return:+.2f}%

**Projected:**
• Completion Date: {pod.projected_completion_date.strftime('%B %Y') if pod.projected_completion_date else 'On track'}

Keep up the great work! Your consistent contributions are making a real difference. 💪
"""
        else:
            required_contribution = pod.calculate_required_monthly_contribution()
            shortfall = required_contribution - pod.monthly_contribution
            
            message = f"""
📊 Monthly Update: {pod.goal_name}

Your Pod needs attention - let's get back on track! 💙

**Current Status:**
• Current Value: ${pod.current_value:,.2f}
• Target Value: ${pod.target_amount:,.2f}
• Progress: {progress}%

**This Month:**
• Return: {monthly_return:+.2f}%

**To Get Back on Track:**
Option 1: Increase monthly contribution by ${shortfall:,.2f} (to ${required_contribution:,.2f}/month)
Option 2: Extend target date by 6-12 months
Option 3: Reduce target amount slightly

Which option works best for you? I'm here to help! 🤝
"""
        
        return message.strip()
    
    def generate_glide_path_notification(
        self,
        pod: PodAggregate,
        transition_date: date,
        new_allocation: Dict[str, Decimal]
    ) -> str:
        """Generate glide path transition notification"""
        months_to_goal = (pod.target_date.year - date.today().year) * 12 + (pod.target_date.month - date.today().month)
        
        message = f"""
🛤️ Glide Path Update: {pod.goal_name}

Your portfolio allocation is being automatically adjusted to match your timeline!

**Timeline:**
• Months to Goal: {months_to_goal}
• Target Date: {pod.target_date.strftime('%B %Y')}

**New Allocation:**
• Equity (Growth): {new_allocation['equity']}%
• Defensive (Protection): {new_allocation['defensive']}%

**Why This Change:**
As you get closer to your goal, I'm gradually shifting to more defensive assets to protect your capital. This is automatic and based on your timeline.

**No Action Needed:**
I'll handle the rebalancing for you. Your goal stays on track! 🎯
"""
        return message.strip()
    
    def generate_circuit_breaker_notification(
        self,
        pod: PodAggregate,
        drawdown: Decimal
    ) -> str:
        """Generate circuit breaker activation notification"""
        message = f"""
🛡️ Protection Activated: {pod.goal_name}

Your portfolio has declined {drawdown}%, triggering our downside protection.

**What I Did:**
• Automatically shifted to 70% defensive, 30% equity
• This protects your capital during market volatility
• Your goal timeline and target remain unchanged

**What This Means:**
• Your portfolio is now more conservative
• Further losses are limited
• Once markets stabilize, I'll gradually return to your optimal allocation

**You're Protected:**
This is exactly why we have circuit breakers - to protect your hard-earned money during market downturns.

**Questions?**
I'm here 24/7 to explain anything. Your goal is still achievable! 💙
"""
        return message.strip()
    
    def answer_question(
        self,
        client_id: str,
        question: str,
        pod: Optional[PodAggregate] = None
    ) -> str:
        """
        Answer client questions about Pods
        
        24/7 Q&A support
        """
        question_lower = question.lower()
        
        # FAQ responses
        if "how" in question_lower and ("work" in question_lower or "works" in question_lower):
            return self._explain_how_pods_work()
        
        elif "fee" in question_lower or "cost" in question_lower:
            return self._explain_fees(pod)
        
        elif "tax" in question_lower:
            return self._explain_tax_benefits()
        
        elif "risk" in question_lower:
            return self._explain_risk_management()
        
        elif "glide path" in question_lower:
            return self._explain_glide_path()
        
        elif "circuit breaker" in question_lower or "protection" in question_lower:
            return self._explain_circuit_breaker()
        
        elif "rebalance" in question_lower or "rebalancing" in question_lower:
            return self._explain_rebalancing()
        
        elif "etf" in question_lower:
            return self._explain_etfs()
        
        elif "contribution" in question_lower:
            return self._explain_contributions(pod)
        
        else:
            return self._general_response()
    
    def _explain_how_pods_work(self) -> str:
        return """
**How Investment Pods Work:**

A Pod is your goal-based investment portfolio. Here's how it works:

1. **You Set Your Goal:** Tell me what you're saving for, how much, and when
2. **I Optimize:** I select the best 6 ETFs to maximize your returns while managing risk
3. **Automatic Management:** I handle everything:
   - Glide path transitions (getting more conservative as you approach your goal)
   - Downside protection (circuit breakers at 15% loss)
   - Rebalancing (keeping your allocation on target)
   - Tax optimization (franking credits, CGT discount)

4. **You Stay in Control:** Adjust contributions, change goals, or ask questions anytime

Think of it as having a professional portfolio manager working for you 24/7! 🤖💼
"""
    
    def _explain_fees(self, pod: Optional[PodAggregate]) -> str:
        if pod:
            return f"""
**Your Pod Fees:**

• ETF Expense Ratios: {pod.total_expense_ratio}% per year
• UltraWealth Management Fee: 0.35% per year (for portfolios $20K-$100K)
• Total Annual Cost: ~{pod.total_expense_ratio + Decimal('0.35')}%

**What You Get:**
✅ AI-powered optimization
✅ Automatic glide path transitions
✅ Downside protection (circuit breakers)
✅ Tax optimization
✅ 24/7 support from me (Anya)
✅ Unlimited rebalancing

**Comparison:**
• Stockspot: 0.66% + ETF fees
• Raiz: $4.50/month ($54/year)
• Traditional advisor: 1-2% per year

You're getting professional management at a fraction of the cost! 💰
"""
        else:
            return "Let me know which Pod you'd like fee information for, and I'll break down the exact costs!"
    
    def _explain_tax_benefits(self) -> str:
        return """
**Australian Tax Benefits in Your Pod:**

🇦🇺 **Franking Credits:**
• Australian companies pay 30% tax on profits
• You get credit for this tax on dividends
• If your tax rate is lower, you get a refund!
• Your Pod targets 2-3% franking yield

💰 **Capital Gains Tax (CGT) Discount:**
• Hold ETFs for >12 months = 50% CGT discount
• I optimize trades to maximize this benefit
• Saves you thousands in taxes!

🏠 **First Home Super Saver (FHSS):**
• If you're saving for a first home, you may be eligible
• Save up to $50,000 inside super with tax benefits
• Ask me if this applies to your goal!

📊 **Tax Loss Harvesting:**
• I identify opportunities to offset capital gains
• Reduces your tax bill automatically

These benefits can add 1-2% to your after-tax returns! 🚀
"""
    
    def _explain_risk_management(self) -> str:
        return """
**How I Manage Risk in Your Pod:**

🛡️ **Circuit Breakers (15% limit):**
• If your Pod drops 15% from peak, I automatically shift to defensive assets
• Protects your capital during market crashes
• Resumes normal allocation once markets stabilize

📉 **Downside Protection:**
• Continuous monitoring during market hours
• Warning alerts at 10% drawdown
• Automatic action at 15% drawdown

🎯 **Glide Path:**
• Automatically shifts to more defensive assets as you approach your goal
• Reduces risk when you need protection most

⚖️ **Diversification:**
• Maximum 6 ETFs across multiple asset classes
• No single ETF >40% of portfolio
• No single provider >60% of portfolio

🔄 **Rebalancing:**
• Keeps your allocation on target
• Sells high, buys low automatically
• Maintains optimal risk/return profile

You're protected at every level! 💪
"""
    
    def _explain_glide_path(self) -> str:
        return """
**Glide Path - Your Automatic Timeline Protection:**

Think of a glide path like landing an airplane - you gradually descend as you approach your destination!

**How It Works:**
• 10 years from goal: 80-90% equity (growth)
• 5 years from goal: 60-70% equity
• 2 years from goal: 30-50% equity
• 1 year from goal: 10-30% equity (mostly defensive)

**Why It Matters:**
• Early on: You have time to recover from market drops, so we invest aggressively
• Close to goal: You need that money soon, so we protect it

**Automatic & Customized:**
• I adjust your allocation automatically based on your timeline
• Different goals have different glide paths (first home vs retirement)
• No action needed from you!

**Example:**
If you're saving $200K for a home in 5 years:
• Year 1-3: 80% equity (maximize growth)
• Year 4: 70% equity (start protecting)
• Year 5: 30% equity (capital preservation)

This way, you get growth when you can afford risk, and protection when you need certainty! 🛬
"""
    
    def _explain_circuit_breaker(self) -> str:
        return """
**Circuit Breaker - Your 15% Protection:**

A circuit breaker is like an emergency brake for your portfolio!

**When It Triggers:**
• Your Pod drops 15% from its peak value
• Example: Peak $100K → Triggers at $85K

**What Happens:**
1. I automatically shift to 70% defensive, 30% equity
2. This limits further losses
3. You get a notification explaining what happened
4. Your goal timeline stays the same

**When It Recovers:**
• Once drawdown recovers to <5%
• And at least 30 days have passed
• I gradually return to your optimal allocation

**Real Example (March 2020):**
• Markets dropped 30%+ during COVID
• Circuit breaker would have triggered at -15%
• Shifted to defensive assets
• Limited total loss to ~18% instead of 30%+
• Saved ~12% of your capital!

**Why 15%?**
• Balances protection with staying invested
• Avoids triggering on normal market volatility
• Protects against major market crashes

You're protected from the worst market outcomes! 🛡️
"""
    
    def _explain_rebalancing(self) -> str:
        return """
**Rebalancing - Keeping Your Pod on Target:**

Rebalancing is like tuning a guitar - keeping everything in harmony!

**When I Rebalance:**
• Any ETF drifts >5% from target weight
• Example: Target 30%, current 35% = 5% drift = rebalance!

**What I Do:**
• Sell ETFs that have grown too large
• Buy ETFs that have shrunk
• Bring everything back to target weights

**Why It Matters:**
• **Sells high, buys low** automatically
• Maintains your optimal risk/return profile
• Prevents concentration risk

**Example:**
Your target: VAS 30%, VGS 30%, NDQ 20%, VAF 20%

After 6 months:
• NDQ grew to 28% (tech stocks did well)
• VAF dropped to 16% (bonds underperformed)

I rebalance:
• Sell some NDQ (taking profits)
• Buy more VAF (buying the dip)
• Back to target: 30/30/20/20

**Cost:**
• Minimal brokerage (~$5-10 per trade)
• Tax-optimized (I prefer >12 month holdings for CGT discount)
• Unlimited rebalancing included!

This discipline adds 0.5-1% to your returns over time! 📈
"""
    
    def _explain_etfs(self) -> str:
        return """
**ETFs - Your Building Blocks:**

ETF = Exchange Traded Fund (like a basket of stocks)

**Why ETFs?**
• **Diversification:** One ETF = hundreds of companies
• **Low Cost:** 0.04-0.50% per year (vs 1-2% for managed funds)
• **Liquid:** Buy/sell anytime on ASX
• **Transparent:** You know exactly what you own

**Example ETFs in Your Pod:**
• **VAS:** Top 300 Australian companies (CBA, BHP, Woolworths, etc.)
• **VGS:** 1,500+ international companies (Apple, Microsoft, Amazon, etc.)
• **NDQ:** Top 100 NASDAQ tech companies
• **VAF:** Australian bonds (defensive, stable income)

**Why Max 6 ETFs?**
• Optimal diversification (more doesn't help much)
• Lower costs (fewer trades)
• Easier to manage
• Research shows 6-8 is the sweet spot!

**Australian Focus:**
• I prioritize Australian ETFs for franking credits
• But also include international for diversification
• Best of both worlds! 🇦🇺🌏
"""
    
    def _explain_contributions(self, pod: Optional[PodAggregate]) -> str:
        if pod:
            return f"""
**Your Contributions:**

• **Current:** ${pod.monthly_contribution:,.2f} per month
• **Required:** ${pod.calculate_required_monthly_contribution():,.2f} per month to stay on track

**How Contributions Work:**
• Automatic monthly debit from your bank account
• I invest immediately into your target allocation
• Dollar-cost averaging (reduces timing risk)

**You Can:**
• Increase/decrease anytime
• Make ad-hoc lump sum contributions
• Pause temporarily (but may affect goal timeline)

**Pro Tips:**
💡 Increase contributions by 5-10% each year (as your income grows)
💡 Contribute bonuses/tax refunds as lump sums
💡 Set up automatic increases on your birthday!

Want to adjust your contributions? Just let me know! 💰
"""
        else:
            return "Let me know which Pod you'd like contribution information for!"
    
    def _general_response(self) -> str:
        return """
I'm here to help! Here are some things you can ask me:

**About Your Pod:**
• "How is my Pod performing?"
• "Am I on track to reach my goal?"
• "What fees am I paying?"

**About Features:**
• "How does the glide path work?"
• "What's a circuit breaker?"
• "How do you optimize for tax?"

**Making Changes:**
• "I want to increase my contributions"
• "Can I change my target date?"
• "How do I withdraw money?"

**General Questions:**
• "What are ETFs?"
• "How do you manage risk?"
• "Why only 6 ETFs?"

What would you like to know? 😊
"""
