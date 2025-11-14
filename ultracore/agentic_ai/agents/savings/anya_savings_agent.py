"""
Anya Savings Agent
AI-powered savings account management and customer advisory
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from uuid import UUID

from ultracore.domains.savings.models.savings_account import SavingsAccount
from ultracore.domains.savings.models.savings_product import SavingsProduct
from ultracore.domains.savings.models.transaction import SavingsTransaction
from ultracore.domains.savings.services.interest_calculator import InterestCalculator


class AnyaSavingsAgent:
    """
    Anya - AI Savings Management Agent
    
    Capabilities:
    - Savings product recommendations based on customer profile
    - Interest optimization strategies
    - Bonus interest condition monitoring and alerts
    - Dormancy prevention (proactive customer engagement)
    - Term deposit maturity management
    - Savings goal tracking and recommendations
    - TFN withholding tax advisory
    - Financial wellness insights
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize Anya Savings Agent
        
        Args:
            llm_client: LLM client for natural language interactions (optional)
        """
        self.llm_client = llm_client
        self.name = "Anya"
        self.role = "Savings Management Specialist"
    
    # ========================================================================
    # PRODUCT RECOMMENDATIONS
    # ========================================================================
    
    def recommend_savings_product(
        self,
        customer_age: int,
        monthly_income: Decimal,
        current_savings: Decimal,
        savings_goal: Optional[Decimal] = None,
        risk_tolerance: str = "moderate",
        available_products: List[SavingsProduct] = None
    ) -> Dict:
        """
        Recommend optimal savings product based on customer profile
        
        Args:
            customer_age: Customer age
            monthly_income: Monthly income
            current_savings: Current savings balance
            savings_goal: Target savings amount (optional)
            risk_tolerance: Risk tolerance (conservative, moderate, aggressive)
            available_products: List of available products
        
        Returns:
            Recommendation with product, reasoning, and projected returns
        """
        if not available_products:
            available_products = []
        
        # Score each product
        product_scores = []
        for product in available_products:
            if not product.is_active:
                continue
            
            score = 0
            reasons = []
            
            # Age-based scoring
            if product.age_restrictions:
                if not product.is_eligible_by_age(customer_age):
                    continue  # Skip ineligible products
                
                # Youth saver bonus for young customers
                if product.product_type == "youth_saver" and customer_age <= 25:
                    score += 20
                    reasons.append("Youth saver product with higher rates for your age group")
            
            # Interest rate scoring
            total_rate = product.calculate_total_interest_rate(bonus_earned=True)
            score += float(total_rate) * 10  # 4.5% rate = 45 points
            reasons.append(f"Competitive interest rate of {total_rate}% p.a.")
            
            # Fee scoring (lower fees = higher score)
            if product.monthly_fee == Decimal("0.00"):
                score += 15
                reasons.append("No monthly account fees")
            elif product.fee_waiver_conditions:
                score += 10
                reasons.append("Monthly fee can be waived with conditions")
            
            # Bonus interest scoring
            if product.bonus_interest_rate > Decimal("0.00"):
                score += 10
                reasons.append(f"Bonus interest of {product.bonus_interest_rate}% available")
            
            # Minimum balance scoring
            if current_savings >= product.minimum_opening_balance:
                score += 5
            else:
                score -= 20  # Penalize if customer can't meet minimum
                reasons.append(f"Requires minimum opening balance of ${product.minimum_opening_balance}")
            
            product_scores.append({
                "product": product,
                "score": score,
                "reasons": reasons,
            })
        
        # Sort by score
        product_scores.sort(key=lambda x: x["score"], reverse=True)
        
        if not product_scores:
            return {
                "recommended_product": None,
                "reasoning": "No suitable products found for your profile",
                "alternatives": [],
            }
        
        # Top recommendation
        top_recommendation = product_scores[0]
        
        # Calculate projected returns
        projection = self._calculate_savings_projection(
            current_balance=current_savings,
            monthly_deposit=monthly_income * Decimal("0.10"),  # Assume 10% savings rate
            annual_rate=top_recommendation["product"].calculate_total_interest_rate(True),
            months=12,
        )
        
        return {
            "recommended_product": {
                "product_id": str(top_recommendation["product"].product_id),
                "product_name": top_recommendation["product"].product_name,
                "product_type": top_recommendation["product"].product_type,
                "interest_rate": float(top_recommendation["product"].base_interest_rate),
                "bonus_rate": float(top_recommendation["product"].bonus_interest_rate),
                "total_rate": float(top_recommendation["product"].calculate_total_interest_rate(True)),
            },
            "score": top_recommendation["score"],
            "reasoning": top_recommendation["reasons"],
            "projected_returns": {
                "period_months": 12,
                "starting_balance": float(current_savings),
                "monthly_deposit": float(monthly_income * Decimal("0.10")),
                "projected_balance": float(projection["final_balance"]),
                "total_interest": float(projection["total_interest"]),
            },
            "alternatives": [
                {
                    "product_name": alt["product"].product_name,
                    "interest_rate": float(alt["product"].calculate_total_interest_rate(True)),
                    "score": alt["score"],
                }
                for alt in product_scores[1:3]  # Top 2 alternatives
            ],
        }
    
    # ========================================================================
    # BONUS INTEREST MONITORING
    # ========================================================================
    
    def check_bonus_eligibility(
        self,
        account: SavingsAccount,
        product: SavingsProduct,
        monthly_transactions: List[SavingsTransaction]
    ) -> Dict:
        """
        Check if customer is on track to earn bonus interest
        
        Args:
            account: Savings account
            product: Savings product
            monthly_transactions: Transactions for current month
        
        Returns:
            Eligibility status with recommendations
        """
        # Calculate monthly deposits and withdrawals
        monthly_deposits = sum(
            t.amount for t in monthly_transactions
            if t.transaction_type == "deposit" and t.amount > 0
        )
        
        withdrawal_count = sum(
            1 for t in monthly_transactions
            if t.transaction_type == "withdrawal"
        )
        
        # Check eligibility
        eligible, conditions = product.check_bonus_eligibility(
            monthly_deposits=monthly_deposits,
            withdrawal_count=withdrawal_count,
            balance=account.balance,
        )
        
        # Calculate potential bonus
        if eligible:
            _, gross_bonus, _, net_bonus = InterestCalculator.calculate_bonus_interest(
                account=account,
                product=product,
                monthly_deposits=monthly_deposits,
                withdrawal_count=withdrawal_count,
            )
        else:
            gross_bonus = Decimal("0.00")
            net_bonus = Decimal("0.00")
        
        # Generate recommendations
        recommendations = []
        if not eligible:
            for condition in product.bonus_conditions:
                if condition.condition_type == "minimum_monthly_deposit":
                    if condition.threshold_amount and monthly_deposits < condition.threshold_amount:
                        shortfall = condition.threshold_amount - monthly_deposits
                        recommendations.append(
                            f"Deposit ${shortfall} more this month to earn bonus interest"
                        )
                
                elif condition.condition_type == "no_withdrawals":
                    if withdrawal_count > 0:
                        recommendations.append(
                            "Avoid withdrawals this month to maintain bonus interest eligibility"
                        )
        
        return {
            "eligible": eligible,
            "conditions_status": conditions,
            "potential_bonus": float(net_bonus),
            "recommendations": recommendations,
            "current_progress": {
                "monthly_deposits": float(monthly_deposits),
                "withdrawal_count": withdrawal_count,
                "current_balance": float(account.balance),
            },
        }
    
    # ========================================================================
    # DORMANCY PREVENTION
    # ========================================================================
    
    def identify_dormancy_risk(
        self,
        account: SavingsAccount,
        dormancy_threshold_days: int = 365
    ) -> Dict:
        """
        Identify accounts at risk of becoming dormant
        
        Args:
            account: Savings account
            dormancy_threshold_days: Days of inactivity before dormancy
        
        Returns:
            Risk assessment with engagement recommendations
        """
        if not account.last_transaction_date:
            days_inactive = (datetime.utcnow() - account.opened_date).days
        else:
            days_inactive = (datetime.utcnow() - account.last_transaction_date).days
        
        days_until_dormant = dormancy_threshold_days - days_inactive
        risk_level = "low"
        
        if days_until_dormant <= 0:
            risk_level = "dormant"
        elif days_until_dormant <= 30:
            risk_level = "critical"
        elif days_until_dormant <= 90:
            risk_level = "high"
        elif days_until_dormant <= 180:
            risk_level = "medium"
        
        # Generate engagement recommendations
        recommendations = []
        if risk_level in ["critical", "high"]:
            recommendations.extend([
                "Make a small deposit to keep your account active",
                "Set up automatic transfers to maintain regular activity",
                "Review your savings goals and adjust your strategy",
            ])
        elif risk_level == "medium":
            recommendations.append(
                "Consider setting up regular deposits to maximize interest earnings"
            )
        
        return {
            "risk_level": risk_level,
            "days_inactive": days_inactive,
            "days_until_dormant": max(0, days_until_dormant),
            "recommendations": recommendations,
            "suggested_actions": [
                {
                    "action": "make_deposit",
                    "description": "Make a deposit of any amount",
                    "impact": "Resets dormancy timer",
                },
                {
                    "action": "setup_auto_transfer",
                    "description": "Set up automatic monthly transfers",
                    "impact": "Prevents future dormancy and grows savings",
                },
            ],
        }
    
    # ========================================================================
    # TFN ADVISORY
    # ========================================================================
    
    def analyze_tfn_impact(
        self,
        account: SavingsAccount,
        projected_annual_interest: Decimal
    ) -> Dict:
        """
        Analyze impact of providing/not providing TFN
        
        Args:
            account: Savings account
            projected_annual_interest: Projected annual interest
        
        Returns:
            TFN impact analysis with recommendations
        """
        # Calculate tax impact
        if account.tfn or account.tfn_exemption:
            withholding_tax = Decimal("0.00")
            recommendation = "You've provided your TFN - no withholding tax applies"
            savings = Decimal("0.00")
        else:
            withholding_tax = projected_annual_interest * Decimal("0.47")
            savings = withholding_tax
            recommendation = (
                f"Provide your TFN to save ${withholding_tax:.2f} in withholding tax. "
                "Interest is still taxable via your personal tax return, but you'll avoid "
                "the 47% upfront withholding."
            )
        
        return {
            "has_tfn": bool(account.tfn or account.tfn_exemption),
            "withholding_tax_rate": float(account.withholding_tax_rate),
            "projected_annual_interest": float(projected_annual_interest),
            "withholding_tax_amount": float(withholding_tax),
            "potential_savings": float(savings),
            "recommendation": recommendation,
            "action_required": not bool(account.tfn or account.tfn_exemption),
        }
    
    # ========================================================================
    # SAVINGS GOALS
    # ========================================================================
    
    def create_savings_plan(
        self,
        current_balance: Decimal,
        target_amount: Decimal,
        target_date: date,
        annual_interest_rate: Decimal,
        current_monthly_deposit: Decimal = Decimal("0.00")
    ) -> Dict:
        """
        Create a savings plan to reach a goal
        
        Args:
            current_balance: Current savings balance
            target_amount: Target savings amount
            target_date: Target date to reach goal
            annual_interest_rate: Expected annual interest rate
            current_monthly_deposit: Current monthly deposit amount
        
        Returns:
            Savings plan with required monthly deposits
        """
        # Calculate months to goal
        months_to_goal = max(1, (target_date - date.today()).days // 30)
        
        # Calculate required monthly deposit
        # Using future value of annuity formula
        monthly_rate = annual_interest_rate / Decimal("100") / Decimal("12")
        
        # FV = PV(1+r)^n + PMT * [(1+r)^n - 1] / r
        # Solve for PMT
        future_value_of_current = current_balance * ((Decimal("1") + monthly_rate) ** months_to_goal)
        remaining_needed = target_amount - future_value_of_current
        
        if monthly_rate > 0:
            required_monthly_deposit = remaining_needed * monthly_rate / (
                ((Decimal("1") + monthly_rate) ** months_to_goal) - Decimal("1")
            )
        else:
            required_monthly_deposit = remaining_needed / Decimal(months_to_goal)
        
        required_monthly_deposit = max(Decimal("0.00"), required_monthly_deposit)
        
        # Check if achievable with current deposits
        is_on_track = current_monthly_deposit >= required_monthly_deposit
        
        # Calculate projected outcome with current deposits
        if current_monthly_deposit > 0:
            projected_balance = future_value_of_current + (
                current_monthly_deposit * (
                    ((Decimal("1") + monthly_rate) ** months_to_goal) - Decimal("1")
                ) / monthly_rate if monthly_rate > 0
                else current_monthly_deposit * Decimal(months_to_goal)
            )
        else:
            projected_balance = future_value_of_current
        
        return {
            "goal": {
                "target_amount": float(target_amount),
                "target_date": target_date.isoformat(),
                "months_to_goal": months_to_goal,
            },
            "current_status": {
                "current_balance": float(current_balance),
                "current_monthly_deposit": float(current_monthly_deposit),
                "projected_balance": float(projected_balance),
            },
            "required_action": {
                "required_monthly_deposit": float(required_monthly_deposit),
                "is_on_track": is_on_track,
                "shortfall": float(max(Decimal("0.00"), required_monthly_deposit - current_monthly_deposit)),
            },
            "recommendations": [
                f"Deposit ${required_monthly_deposit:.2f} per month to reach your goal",
                f"Your savings will grow to ${projected_balance:.2f} with current deposits",
                "Consider setting up automatic transfers to stay on track",
            ] if not is_on_track else [
                "You're on track to reach your savings goal!",
                f"Continue depositing ${current_monthly_deposit:.2f} per month",
                f"You'll reach ${target_amount:.2f} by {target_date.isoformat()}",
            ],
        }
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _calculate_savings_projection(
        self,
        current_balance: Decimal,
        monthly_deposit: Decimal,
        annual_rate: Decimal,
        months: int
    ) -> Dict:
        """Calculate savings projection with compound interest"""
        monthly_rate = annual_rate / Decimal("100") / Decimal("12")
        
        # Future value of current balance
        fv_current = current_balance * ((Decimal("1") + monthly_rate) ** months)
        
        # Future value of monthly deposits (annuity)
        if monthly_rate > 0:
            fv_deposits = monthly_deposit * (
                ((Decimal("1") + monthly_rate) ** months) - Decimal("1")
            ) / monthly_rate
        else:
            fv_deposits = monthly_deposit * Decimal(months)
        
        final_balance = fv_current + fv_deposits
        total_deposits = monthly_deposit * Decimal(months)
        total_interest = final_balance - current_balance - total_deposits
        
        return {
            "final_balance": final_balance,
            "total_deposits": total_deposits,
            "total_interest": total_interest,
        }
