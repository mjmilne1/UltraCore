"""Financial Planning - Goal-Based Investment Planning"""
from typing import Dict, List
from decimal import Decimal
from datetime import date
from dateutil.relativedelta import relativedelta


class FinancialPlanner:
    """
    Goal-based financial planning.
    
    Features:
    - Retirement planning
    - Home purchase planning
    - Education planning
    - Goal tracking
    - Cash flow projections
    - Savings recommendations
    
    Australian Context:
    - Superannuation (retirement savings)
    - First Home Buyer schemes
    - HECS/HELP education debt
    - Centrelink age pension
    """
    
    def __init__(self):
        pass
    
    async def create_retirement_plan(
        self,
        current_age: int,
        retirement_age: int,
        current_savings: Decimal,
        monthly_contribution: Decimal,
        desired_retirement_income: Decimal,
        super_balance: Decimal = Decimal("0.00")
    ) -> Dict:
        """
        Create retirement financial plan.
        
        Australian Retirement:
        - Preservation age: 60
        - Age pension age: 67
        - Superannuation (concessional tax)
        - Account-based pensions
        """
        
        years_to_retirement = retirement_age - current_age
        
        # Calculate projected balance at retirement
        # Assuming 7% p.a. return
        return_rate = Decimal("0.07")
        
        # Future value of current savings
        fv_savings = current_savings * (1 + return_rate) ** years_to_retirement
        
        # Future value of contributions (annuity)
        annual_contribution = monthly_contribution * 12
        fv_contributions = annual_contribution * (
            ((1 + return_rate) ** years_to_retirement - 1) / return_rate
        )
        
        # Super (assuming 9% p.a. in super due to lower tax)
        super_return = Decimal("0.09")
        fv_super = super_balance * (1 + super_return) ** years_to_retirement
        
        total_at_retirement = fv_savings + fv_contributions + fv_super
        
        # Calculate sustainable withdrawal
        # 4% rule (conservative)
        sustainable_income = total_at_retirement * Decimal("0.04") / 12
        
        # Age pension (current max ~$2,500/month for couple)
        age_pension = Decimal("1250")  # Per person
        
        total_retirement_income = sustainable_income + age_pension
        
        # Shortfall analysis
        shortfall = desired_retirement_income - total_retirement_income
        
        return {
            "current_situation": {
                "age": current_age,
                "savings": float(current_savings),
                "super_balance": float(super_balance),
                "monthly_contribution": float(monthly_contribution)
            },
            "retirement_goal": {
                "retirement_age": retirement_age,
                "years_to_retirement": years_to_retirement,
                "desired_monthly_income": float(desired_retirement_income)
            },
            "projections": {
                "total_at_retirement": float(total_at_retirement),
                "from_savings": float(fv_savings),
                "from_contributions": float(fv_contributions),
                "from_super": float(fv_super)
            },
            "retirement_income": {
                "from_investments": float(sustainable_income),
                "from_age_pension": float(age_pension),
                "total_monthly": float(total_retirement_income),
                "vs_goal": float(total_retirement_income - desired_retirement_income)
            },
            "analysis": {
                "on_track": shortfall <= 0,
                "shortfall_monthly": float(max(shortfall, Decimal("0"))),
                "surplus_monthly": float(max(-shortfall, Decimal("0")))
            },
            "recommendations": self._get_retirement_recommendations(
                shortfall,
                monthly_contribution,
                years_to_retirement
            )
        }
    
    def _get_retirement_recommendations(
        self,
        shortfall: Decimal,
        current_contribution: Decimal,
        years_to_retirement: int
    ) -> List[str]:
        """Get retirement planning recommendations."""
        
        recommendations = []
        
        if shortfall > 0:
            # Calculate additional contribution needed
            return_rate = Decimal("0.07")
            additional_annual = shortfall * 12 / Decimal("0.04")  # Capital needed
            additional_monthly = (additional_annual * return_rate) / (
                ((1 + return_rate) ** years_to_retirement - 1)
            )
            
            recommendations.append(
                f"Increase monthly contributions by ${float(additional_monthly):,.0f} to meet goal"
            )
            recommendations.append(
                f"Or work {years_to_retirement - 2} more years to build larger balance"
            )
            recommendations.append(
                "Consider salary sacrificing to super (tax benefits)"
            )
        else:
            recommendations.append(
                "? On track for retirement goal!"
            )
            recommendations.append(
                "Consider increasing lifestyle spending or retiring earlier"
            )
        
        recommendations.append(
            "Review super fund performance (aim for top quartile)"
        )
        recommendations.append(
            "Consider spouse contributions for tax offset"
        )
        recommendations.append(
            "Plan for aged care costs (~$100K+ for bond)"
        )
        
        return recommendations
    
    async def create_home_purchase_plan(
        self,
        target_price: Decimal,
        current_savings: Decimal,
        monthly_savings: Decimal,
        deposit_percentage: Decimal = Decimal("0.20")
    ) -> Dict:
        """
        Create home purchase financial plan.
        
        Australian First Home:
        - First Home Buyer schemes
        - Stamp duty concessions
        - First Home Super Saver Scheme
        - Minimum deposit: 5% (LMI required)
        - Recommended: 20% (avoid LMI)
        """
        
        # Calculate required deposit
        required_deposit = target_price * deposit_percentage
        
        # Additional costs
        stamp_duty = self._calculate_stamp_duty(target_price)
        conveyancing = Decimal("2000")
        building_inspection = Decimal("500")
        other_costs = Decimal("1000")
        
        total_upfront = required_deposit + stamp_duty + conveyancing + building_inspection + other_costs
        
        # Calculate time to save
        shortfall = total_upfront - current_savings
        
        if shortfall > 0 and monthly_savings > 0:
            months_to_save = int(shortfall / monthly_savings) + 1
            years_to_save = months_to_save / 12
        else:
            months_to_save = 0
            years_to_save = 0
        
        # Loan details
        loan_amount = target_price - required_deposit
        monthly_repayment = self._calculate_mortgage_repayment(
            loan_amount,
            Decimal("0.065"),  # 6.5% interest
            30  # 30 year loan
        )
        
        return {
            "home_goal": {
                "target_price": float(target_price),
                "deposit_percentage": float(deposit_percentage * 100),
                "required_deposit": float(required_deposit)
            },
            "upfront_costs": {
                "deposit": float(required_deposit),
                "stamp_duty": float(stamp_duty),
                "conveyancing": float(conveyancing),
                "inspections": float(building_inspection),
                "other": float(other_costs),
                "total": float(total_upfront)
            },
            "savings_plan": {
                "current_savings": float(current_savings),
                "shortfall": float(max(shortfall, Decimal("0"))),
                "monthly_savings": float(monthly_savings),
                "months_to_save": months_to_save,
                "years_to_save": round(years_to_save, 1),
                "ready_by": (date.today() + relativedelta(months=months_to_save)).isoformat() if months_to_save > 0 else "Ready now!"
            },
            "loan_details": {
                "loan_amount": float(loan_amount),
                "interest_rate": 6.5,
                "loan_term_years": 30,
                "monthly_repayment": float(monthly_repayment),
                "total_interest": float(monthly_repayment * 360 - loan_amount)
            },
            "recommendations": [
                f"Save ${float(monthly_savings):,.0f}/month for {years_to_save:.1f} years" if months_to_save > 0 else "Ready to buy!",
                "Check First Home Buyer schemes (stamp duty savings)",
                "Consider First Home Super Saver Scheme (up to $50K)",
                "Get pre-approval for loan (know your budget)",
                "Build genuine savings (3+ months history)",
                "Allow buffer for unexpected costs"
            ]
        }
    
    def _calculate_stamp_duty(self, property_price: Decimal) -> Decimal:
        """
        Calculate stamp duty (NSW rates).
        
        Varies by state. This uses NSW as example.
        First home buyers may get concessions.
        """
        
        # Simplified NSW rates
        if property_price <= Decimal("14000"):
            return property_price * Decimal("0.0125")
        elif property_price <= Decimal("32000"):
            return Decimal("175") + (property_price - Decimal("14000")) * Decimal("0.015")
        elif property_price <= Decimal("85000"):
            return Decimal("445") + (property_price - Decimal("32000")) * Decimal("0.0175")
        elif property_price <= Decimal("319000"):
            return Decimal("1372.50") + (property_price - Decimal("85000")) * Decimal("0.035")
        elif property_price <= Decimal("1064000"):
            return Decimal("9562.50") + (property_price - Decimal("319000")) * Decimal("0.045")
        else:
            return Decimal("43087.50") + (property_price - Decimal("1064000")) * Decimal("0.055")
    
    def _calculate_mortgage_repayment(
        self,
        loan_amount: Decimal,
        interest_rate: Decimal,
        loan_term_years: int
    ) -> Decimal:
        """Calculate monthly mortgage repayment."""
        
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12
        
        if monthly_rate > 0:
            repayment = loan_amount * (
                monthly_rate * (1 + monthly_rate) ** num_payments
            ) / (
                (1 + monthly_rate) ** num_payments - 1
            )
        else:
            repayment = loan_amount / num_payments
        
        return repayment.quantize(Decimal("0.01"))
