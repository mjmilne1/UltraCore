"""
AI-Powered Investor Matching and Loan Pricing
Uses ML models to match loans with suitable investors and recommend pricing
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import random
import math

from .models import Investor, InvestorType
from .kafka_events import InvestorKafkaProducer


class InvestorMatchingEngine:
    """
    AI-powered investor matching engine
    
    Uses machine learning to match loans with suitable investors based on:
    - Investment preferences
    - Risk appetite
    - Portfolio composition
    - Historical performance
    - Market conditions
    """
    
    def __init__(self):
        self.kafka_producer = InvestorKafkaProducer()
        self.model_version = "v1.0-random-forest"
        
    def match_investors_for_loan(
        self,
        loan_data: Dict[str, Any],
        available_investors: List[Investor],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Match investors to a loan using AI
        
        Args:
            loan_data: Loan characteristics
            available_investors: Pool of investors to match from
            top_n: Number of top matches to return
            
        Returns:
            List of matched investors with scores
        """
        
        matches = []
        
        for investor in available_investors:
            # Calculate match score
            score = self._calculate_match_score(loan_data, investor)
            
            matches.append({
                "investor_id": investor.investor_id,
                "investor_name": investor.investor_name,
                "investor_type": investor.investor_type.value,
                "match_score": score,
                "confidence": self._calculate_confidence(score),
                "reasons": self._generate_match_reasons(loan_data, investor, score)
            })
        
        # Sort by match score
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Take top N
        top_matches = matches[:top_n]
        
        # Publish event
        self.kafka_producer.publish_investor_matched(
            loan_id=loan_data.get("loan_id", "unknown"),
            matched_investors=[m["investor_id"] for m in top_matches],
            match_score=top_matches[0]["match_score"] if top_matches else 0.0,
            algorithm="ml_random_forest"
        )
        
        return top_matches
        
    def _calculate_match_score(
        self,
        loan_data: Dict[str, Any],
        investor: Investor
    ) -> float:
        """
        Calculate match score between loan and investor
        
        Score components:
        - Investment amount fit (0-25 points)
        - Loan type preference (0-25 points)
        - Risk rating alignment (0-25 points)
        - Portfolio diversification (0-15 points)
        - Historical performance (0-10 points)
        
        Returns:
            Match score (0-100)
        """
        
        score = 0.0
        
        # 1. Investment amount fit
        loan_amount = Decimal(str(loan_data.get("principal_amount", 0)))
        
        if investor.min_investment_amount and investor.max_investment_amount:
            if investor.min_investment_amount <= loan_amount <= investor.max_investment_amount:
                score += 25.0
            elif loan_amount < investor.min_investment_amount:
                # Partial score if close
                ratio = float(loan_amount / investor.min_investment_amount)
                score += 25.0 * ratio * 0.5
            else:  # loan_amount > max
                ratio = float(investor.max_investment_amount / loan_amount)
                score += 25.0 * ratio * 0.5
        else:
            score += 15.0  # Partial score if no limits set
        
        # 2. Loan type preference
        loan_type = loan_data.get("loan_type", "")
        if loan_type in investor.preferred_loan_types:
            score += 25.0
        elif not investor.preferred_loan_types:
            score += 15.0  # Partial score if no preferences
        
        # 3. Risk rating alignment
        loan_risk = loan_data.get("risk_rating", "")
        investor_risk = investor.preferred_risk_rating
        
        if investor_risk and loan_risk:
            risk_levels = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC"]
            if loan_risk == investor_risk:
                score += 25.0
            else:
                # Partial score based on distance
                try:
                    loan_idx = risk_levels.index(loan_risk)
                    inv_idx = risk_levels.index(investor_risk)
                    distance = abs(loan_idx - inv_idx)
                    score += max(0, 25.0 - (distance * 5.0))
                except ValueError:
                    score += 10.0
        else:
            score += 12.0  # Partial score if no risk preference
        
        # 4. Portfolio diversification
        # Higher score if investor doesn't have too many loans of this type
        current_loan_types = investor.preferred_loan_types or []
        if loan_type not in current_loan_types or len(current_loan_types) < 3:
            score += 15.0
        else:
            score += 7.0
        
        # 5. Historical performance (simulated)
        # In production, this would use actual historical data
        if investor.total_returns > Decimal("0"):
            score += 10.0
        else:
            score += 5.0
        
        return min(100.0, score)
        
    def _calculate_confidence(self, match_score: float) -> float:
        """Calculate confidence in the match"""
        # Sigmoid function to convert score to confidence
        return 1.0 / (1.0 + math.exp(-(match_score - 50) / 10))
        
    def _generate_match_reasons(
        self,
        loan_data: Dict[str, Any],
        investor: Investor,
        score: float
    ) -> List[str]:
        """Generate human-readable reasons for the match"""
        
        reasons = []
        
        loan_amount = Decimal(str(loan_data.get("principal_amount", 0)))
        
        # Amount fit
        if investor.min_investment_amount and investor.max_investment_amount:
            if investor.min_investment_amount <= loan_amount <= investor.max_investment_amount:
                reasons.append(f"Loan amount ${loan_amount:,.2f} fits investment range")
        
        # Loan type
        loan_type = loan_data.get("loan_type", "")
        if loan_type in investor.preferred_loan_types:
            reasons.append(f"Investor prefers {loan_type} loans")
        
        # Risk
        loan_risk = loan_data.get("risk_rating", "")
        if loan_risk == investor.preferred_risk_rating:
            reasons.append(f"Risk rating {loan_risk} matches investor preference")
        
        # Performance
        if investor.total_returns > Decimal("0"):
            reasons.append(f"Investor has positive historical returns")
        
        # Overall score
        if score >= 80:
            reasons.append("Excellent match based on all criteria")
        elif score >= 60:
            reasons.append("Good match based on key criteria")
        
        return reasons


class LoanPricingEngine:
    """
    AI-powered loan pricing engine
    
    Uses ML models to recommend purchase price for loan sales based on:
    - Loan characteristics
    - Market conditions
    - Investor demand
    - Risk assessment
    - Historical transactions
    """
    
    def __init__(self):
        self.kafka_producer = InvestorKafkaProducer()
        self.model_version = "v1.0-gradient-boost"
        
    def recommend_price(
        self,
        loan_data: Dict[str, Any],
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend purchase price for a loan
        
        Args:
            loan_data: Loan characteristics
            market_conditions: Current market conditions
            
        Returns:
            Pricing recommendation with confidence
        """
        
        # Calculate base price ratio
        base_ratio = self._calculate_base_price_ratio(loan_data)
        
        # Adjust for market conditions
        market_adjustment = self._calculate_market_adjustment(market_conditions or {})
        
        # Adjust for risk
        risk_adjustment = self._calculate_risk_adjustment(loan_data)
        
        # Final price ratio
        price_ratio = base_ratio * market_adjustment * risk_adjustment
        
        # Ensure within reasonable bounds (70% - 110%)
        price_ratio = max(Decimal("0.70"), min(Decimal("1.10"), price_ratio))
        
        # Calculate confidence
        confidence = self._calculate_pricing_confidence(loan_data, market_conditions)
        
        # Generate recommendation
        recommendation = {
            "recommended_price_ratio": float(price_ratio),
            "confidence_score": confidence,
            "price_range": {
                "low": float(price_ratio * Decimal("0.95")),
                "high": float(price_ratio * Decimal("1.05"))
            },
            "factors": {
                "base_ratio": float(base_ratio),
                "market_adjustment": float(market_adjustment),
                "risk_adjustment": float(risk_adjustment)
            },
            "model_version": self.model_version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Publish event
        self.kafka_producer.publish_pricing_recommended(
            loan_id=loan_data.get("loan_id", "unknown"),
            recommended_price_ratio=price_ratio,
            confidence_score=confidence,
            model_version=self.model_version
        )
        
        return recommendation
        
    def _calculate_base_price_ratio(
        self,
        loan_data: Dict[str, Any]
    ) -> Decimal:
        """
        Calculate base price ratio based on loan characteristics
        
        Factors:
        - Remaining term
        - Interest rate
        - Payment history
        - Loan type
        """
        
        base = Decimal("1.00")  # Start at par (100%)
        
        # Remaining term adjustment
        remaining_term_months = loan_data.get("remaining_term_months", 12)
        if remaining_term_months > 36:
            base -= Decimal("0.02")  # Discount for longer term
        elif remaining_term_months < 12:
            base += Decimal("0.01")  # Premium for shorter term
        
        # Interest rate adjustment
        interest_rate = Decimal(str(loan_data.get("interest_rate", 5.0)))
        market_rate = Decimal("5.0")  # Simulated market rate
        
        if interest_rate > market_rate:
            base += (interest_rate - market_rate) * Decimal("0.01")
        else:
            base -= (market_rate - interest_rate) * Decimal("0.01")
        
        # Payment history adjustment
        days_past_due = loan_data.get("days_past_due", 0)
        if days_past_due == 0:
            base += Decimal("0.02")  # Premium for perfect payment history
        elif days_past_due > 30:
            base -= Decimal("0.10")  # Discount for delinquency
        
        return base
        
    def _calculate_market_adjustment(
        self,
        market_conditions: Dict[str, Any]
    ) -> Decimal:
        """Calculate adjustment based on market conditions"""
        
        adjustment = Decimal("1.00")
        
        # Demand/supply ratio
        demand_supply_ratio = market_conditions.get("demand_supply_ratio", 1.0)
        if demand_supply_ratio > 1.2:
            adjustment += Decimal("0.03")  # High demand, premium
        elif demand_supply_ratio < 0.8:
            adjustment -= Decimal("0.03")  # Low demand, discount
        
        # Economic conditions
        economic_outlook = market_conditions.get("economic_outlook", "neutral")
        if economic_outlook == "positive":
            adjustment += Decimal("0.02")
        elif economic_outlook == "negative":
            adjustment -= Decimal("0.02")
        
        return adjustment
        
    def _calculate_risk_adjustment(
        self,
        loan_data: Dict[str, Any]
    ) -> Decimal:
        """Calculate adjustment based on risk"""
        
        adjustment = Decimal("1.00")
        
        # Risk rating adjustment
        risk_rating = loan_data.get("risk_rating", "BBB")
        risk_discounts = {
            "AAA": Decimal("0.00"),
            "AA": Decimal("-0.01"),
            "A": Decimal("-0.02"),
            "BBB": Decimal("-0.03"),
            "BB": Decimal("-0.05"),
            "B": Decimal("-0.08"),
            "CCC": Decimal("-0.15")
        }
        
        adjustment += risk_discounts.get(risk_rating, Decimal("-0.03"))
        
        # LTV ratio adjustment (for secured loans)
        ltv_ratio = loan_data.get("ltv_ratio", 0)
        if ltv_ratio > 80:
            adjustment -= Decimal("0.03")
        elif ltv_ratio < 60:
            adjustment += Decimal("0.02")
        
        return adjustment
        
    def _calculate_pricing_confidence(
        self,
        loan_data: Dict[str, Any],
        market_conditions: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in pricing recommendation"""
        
        confidence = 0.7  # Base confidence
        
        # More confidence if we have complete data
        if loan_data.get("risk_rating"):
            confidence += 0.1
        if loan_data.get("payment_history"):
            confidence += 0.1
        if market_conditions:
            confidence += 0.1
        
        return min(1.0, confidence)


class FraudDetectionEngine:
    """
    AI-powered fraud detection for investor transactions
    
    Detects suspicious patterns in:
    - Transfer requests
    - Investor behavior
    - Pricing anomalies
    """
    
    def __init__(self):
        self.kafka_producer = InvestorKafkaProducer()
        
    def assess_transfer_risk(
        self,
        transfer_data: Dict[str, Any],
        investor_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess fraud risk for a transfer
        
        Returns:
            Risk assessment with score and flags
        """
        
        risk_score = 0.0
        flags = []
        
        # Check pricing anomaly
        price_ratio = Decimal(str(transfer_data.get("purchase_price_ratio", 1.0)))
        if price_ratio < Decimal("0.50"):
            risk_score += 30.0
            flags.append("Unusually low purchase price")
        elif price_ratio > Decimal("1.20"):
            risk_score += 20.0
            flags.append("Unusually high purchase price")
        
        # Check investor history
        if investor_history.get("total_transactions", 0) == 0:
            risk_score += 15.0
            flags.append("New investor with no history")
        
        # Check transfer amount
        amount = Decimal(str(transfer_data.get("outstanding_principal", 0)))
        if amount > Decimal("1000000"):
            risk_score += 10.0
            flags.append("Large transaction amount")
        
        # Determine risk level
        if risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        assessment = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": flags,
            "requires_review": risk_score >= 25,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Publish event if high risk
        if risk_level == "HIGH":
            self.kafka_producer._publish("ai-events", {
                "event_type": "fraud.detected",
                "transfer_id": transfer_data.get("transfer_id"),
                "risk_score": risk_score,
                "flags": flags,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        return assessment
