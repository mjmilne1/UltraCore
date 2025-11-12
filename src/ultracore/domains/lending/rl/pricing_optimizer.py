"""RL: Dynamic Loan Pricing Optimization"""
import numpy as np
from typing import Dict, Tuple
from decimal import Decimal

from ultracore.rl.base import BaseRLAgent


class LoanPricingOptimizer(BaseRLAgent):
    """
    Reinforcement learning for optimal loan pricing.
    
    Goal: Maximize profitability while maintaining approval rates
    
    State:
    - Customer credit score
    - Loan amount and term
    - Current market rates
    - Competition rates
    - Default risk
    - Target market segment
    
    Actions:
    - Interest rate to offer (within acceptable range)
    
    Reward:
    - Profit from approved loans
    - Penalty for defaults
    - Penalty for declined applications (opportunity cost)
    
    Australian Market Context:
    - RBA cash rate influences pricing
    - Competitive market (comparison sites)
    - Regulatory constraints (NCCP responsible lending)
    """
    
    def __init__(self):
        super().__init__(
            agent_name="loan_pricing_optimizer",
            state_dim=10,
            action_dim=20  # 20 different rate tiers
        )
        
        # Australian market rates (2024)
        self.base_rates = {
            "personal_loan": Decimal("8.00"),  # 8% p.a.
            "home_loan_owner_occupied": Decimal("6.00"),  # 6% p.a.
            "home_loan_investment": Decimal("6.50"),  # 6.5% p.a.
            "business_loan": Decimal("7.50"),  # 7.5% p.a.
            "loc": Decimal("9.00")  # 9% p.a.
        }
        
        # Rate adjustments based on risk
        self.risk_premiums = {
            "excellent": Decimal("0.00"),  # No premium
            "very_good": Decimal("0.50"),  # +0.5%
            "good": Decimal("1.00"),  # +1.0%
            "fair": Decimal("2.00"),  # +2.0%
            "poor": Decimal("4.00")  # +4.0%
        }
    
    async def optimize_rate(
        self,
        loan_type: str,
        loan_amount: Decimal,
        term_months: int,
        credit_score: int,
        risk_band: str,
        lvr: Decimal = None
    ) -> Dict:
        """
        Calculate optimal interest rate for loan.
        
        Balances:
        - Competitive pricing (approval rate)
        - Profitability (interest income)
        - Risk management (default protection)
        """
        
        # Get base rate for loan type
        base_rate = self.base_rates.get(loan_type, Decimal("10.00"))
        
        # Risk premium
        risk_premium = self.risk_premiums.get(risk_band, Decimal("3.00"))
        
        # LVR adjustment (for home loans)
        lvr_adjustment = Decimal("0.00")
        if lvr:
            if lvr > Decimal("0.95"):  # > 95% LVR
                lvr_adjustment = Decimal("0.50")
            elif lvr > Decimal("0.90"):  # > 90% LVR
                lvr_adjustment = Decimal("0.30")
            elif lvr > Decimal("0.80"):  # > 80% LVR
                lvr_adjustment = Decimal("0.20")
        
        # Loan amount discount (larger loans = lower rates)
        amount_discount = Decimal("0.00")
        if loan_amount > Decimal("500000"):
            amount_discount = Decimal("0.25")
        elif loan_amount > Decimal("250000"):
            amount_discount = Decimal("0.15")
        
        # Term adjustment (longer term = slightly higher)
        term_adjustment = Decimal("0.00")
        if term_months > 300:  # > 25 years
            term_adjustment = Decimal("0.10")
        
        # Calculate final rate
        final_rate = (
            base_rate +
            risk_premium +
            lvr_adjustment -
            amount_discount +
            term_adjustment
        )
        
        # Floor and ceiling
        final_rate = max(final_rate, Decimal("5.00"))  # Floor
        final_rate = min(final_rate, Decimal("20.00"))  # Ceiling
        
        # Calculate comparison rate (includes fees)
        comparison_rate = self._calculate_comparison_rate(
            final_rate,
            loan_amount,
            term_months
        )
        
        # Expected profit
        expected_profit = self._calculate_expected_profit(
            loan_amount,
            final_rate,
            term_months,
            risk_band
        )
        
        return {
            "interest_rate": float(final_rate),
            "comparison_rate": float(comparison_rate),
            "base_rate": float(base_rate),
            "risk_premium": float(risk_premium),
            "adjustments": {
                "lvr_adjustment": float(lvr_adjustment),
                "amount_discount": float(amount_discount),
                "term_adjustment": float(term_adjustment)
            },
            "expected_profit": float(expected_profit),
            "approval_probability": self._estimate_approval_probability(final_rate, risk_band)
        }
    
    def _calculate_comparison_rate(
        self,
        interest_rate: Decimal,
        loan_amount: Decimal,
        term_months: int
    ) -> Decimal:
        """
        Calculate comparison rate (Australian requirement).
        
        Includes all fees in effective rate.
        """
        # Typical fees
        establishment_fee = Decimal("500")
        monthly_fee = Decimal("10")
        
        total_fees = establishment_fee + (monthly_fee * term_months)
        
        # Effective rate including fees
        # Simplified calculation
        fee_rate_adjustment = (total_fees / loan_amount) * Decimal("100") / (term_months / 12)
        
        comparison_rate = interest_rate + fee_rate_adjustment
        
        return comparison_rate
    
    def _calculate_expected_profit(
        self,
        loan_amount: Decimal,
        interest_rate: Decimal,
        term_months: int,
        risk_band: str
    ) -> Decimal:
        """Calculate expected profit from loan."""
        
        # Total interest over life of loan (simplified)
        total_interest = loan_amount * (interest_rate / Decimal("100")) * (term_months / 12)
        
        # Cost of funds (bank's borrowing cost)
        cost_of_funds_rate = Decimal("4.00")  # 4% (RBA + margin)
        cost_of_funds = loan_amount * (cost_of_funds_rate / Decimal("100")) * (term_months / 12)
        
        # Expected loss (based on default probability)
        default_probabilities = {
            "excellent": Decimal("0.01"),  # 1%
            "very_good": Decimal("0.02"),  # 2%
            "good": Decimal("0.05"),  # 5%
            "fair": Decimal("0.10"),  # 10%
            "poor": Decimal("0.20")  # 20%
        }
        
        default_prob = default_probabilities.get(risk_band, Decimal("0.10"))
        expected_loss = loan_amount * default_prob * Decimal("0.5")  # 50% recovery
        
        # Profit
        profit = total_interest - cost_of_funds - expected_loss
        
        return profit
    
    def _estimate_approval_probability(self, rate: Decimal, risk_band: str) -> float:
        """
        Estimate probability customer will accept the rate.
        
        Higher rates = lower acceptance.
        """
        
        # Base acceptance rates
        base_acceptance = {
            "excellent": 0.90,
            "very_good": 0.85,
            "good": 0.75,
            "fair": 0.60,
            "poor": 0.40
        }
        
        acceptance = base_acceptance.get(risk_band, 0.70)
        
        # Adjust for rate competitiveness
        market_rate = Decimal("8.00")
        if rate < market_rate:
            acceptance += 0.05  # More competitive
        elif rate > market_rate + Decimal("2.00"):
            acceptance -= 0.15  # Less competitive
        
        return max(min(acceptance, 1.0), 0.0)
