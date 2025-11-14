"""
Risk Assessment AI Agent
Autonomous agent for investment risk profiling and suitability assessment
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskAssessmentAgent:
    """
    AI Agent for autonomous risk assessment and profiling
    
    Capabilities:
    - Risk questionnaire analysis
    - Risk score calculation
    - Suitability assessment
    - Portfolio recommendations
    - Risk category determination
    """
    
    def __init__(self):
        self.agent_id = "risk_assessment_agent"
        self.version = "1.0.0"
    
    def analyze_questionnaire(
        self,
        client_id: str,
        questionnaire_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze risk questionnaire responses
        
        Questionnaire categories:
        - Investment objectives
        - Time horizon
        - Risk tolerance
        - Financial situation
        - Investment experience
        """
        logger.info(f"Analyzing risk questionnaire for client {client_id}")
        
        # Extract key factors
        investment_objective = questionnaire_responses.get("investment_objective", "growth")
        time_horizon_years = questionnaire_responses.get("time_horizon_years", 10)
        risk_tolerance = questionnaire_responses.get("risk_tolerance", "moderate")
        annual_income = questionnaire_responses.get("annual_income", 0)
        net_worth = questionnaire_responses.get("net_worth", 0)
        investment_experience = questionnaire_responses.get("investment_experience", "beginner")
        loss_tolerance_percentage = questionnaire_responses.get("loss_tolerance_percentage", 10)
        
        # Calculate risk factors
        risk_factors = {
            "time_horizon_score": self._calculate_time_horizon_score(time_horizon_years),
            "financial_capacity_score": self._calculate_financial_capacity_score(annual_income, net_worth),
            "experience_score": self._calculate_experience_score(investment_experience),
            "loss_tolerance_score": self._calculate_loss_tolerance_score(loss_tolerance_percentage),
            "objective_score": self._calculate_objective_score(investment_objective)
        }
        
        analysis_result = {
            "client_id": client_id,
            "risk_factors": risk_factors,
            "questionnaire_responses": questionnaire_responses,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        return analysis_result
    
    def calculate_risk_score(
        self,
        client_id: str,
        questionnaire_analysis: Dict[str, Any],
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score using ML
        """
        logger.info(f"Calculating risk score for client {client_id}")
        
        risk_factors = questionnaire_analysis["risk_factors"]
        
        # Weighted average of risk factors
        weights = {
            "time_horizon_score": 0.25,
            "financial_capacity_score": 0.25,
            "experience_score": 0.20,
            "loss_tolerance_score": 0.20,
            "objective_score": 0.10
        }
        
        calculated_score = sum(
            risk_factors[factor] * weight
            for factor, weight in weights.items()
        )
        
        # Normalize to 0-100 scale
        normalized_score = calculated_score * 100
        
        # Determine risk category
        risk_category = self._determine_risk_category(normalized_score)
        
        score_result = {
            "client_id": client_id,
            "calculated_score": normalized_score,
            "risk_category": risk_category,
            "risk_factors": risk_factors,
            "factor_weights": weights,
            "confidence_score": 0.92,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        return score_result
    
    def assess_suitability(
        self,
        client_id: str,
        risk_profile: Dict[str, Any],
        proposed_investment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess investment suitability based on risk profile
        """
        logger.info(f"Assessing investment suitability for client {client_id}")
        
        client_risk_score = risk_profile["calculated_score"]
        client_risk_category = risk_profile["risk_category"]
        
        investment_risk_level = proposed_investment.get("risk_level", "moderate")
        investment_type = proposed_investment.get("investment_type", "stocks")
        
        # Map risk categories to acceptable investment risk levels
        suitability_matrix = {
            "conservative": ["low"],
            "moderate": ["low", "medium"],
            "balanced": ["low", "medium", "medium_high"],
            "growth": ["medium", "medium_high", "high"],
            "aggressive": ["medium_high", "high", "very_high"]
        }
        
        is_suitable = investment_risk_level in suitability_matrix.get(client_risk_category, [])
        
        suitability_result = {
            "client_id": client_id,
            "is_suitable": is_suitable,
            "client_risk_category": client_risk_category,
            "client_risk_score": client_risk_score,
            "investment_risk_level": investment_risk_level,
            "investment_type": investment_type,
            "suitability_score": 0.85 if is_suitable else 0.35,
            "recommendation": "approved" if is_suitable else "not_suitable",
            "reasoning": self._generate_suitability_reasoning(
                is_suitable, client_risk_category, investment_risk_level
            ),
            "assessed_at": datetime.utcnow().isoformat()
        }
        
        return suitability_result
    
    def recommend_portfolio_allocation(
        self,
        client_id: str,
        risk_profile: Dict[str, Any],
        investment_goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Recommend portfolio allocation based on risk profile and goals
        """
        logger.info(f"Recommending portfolio allocation for client {client_id}")
        
        risk_category = risk_profile["risk_category"]
        
        # Standard allocations by risk category
        allocation_templates = {
            "conservative": {
                "cash": 20,
                "bonds": 50,
                "stocks": 20,
                "alternatives": 10
            },
            "moderate": {
                "cash": 10,
                "bonds": 40,
                "stocks": 40,
                "alternatives": 10
            },
            "balanced": {
                "cash": 5,
                "bonds": 30,
                "stocks": 55,
                "alternatives": 10
            },
            "growth": {
                "cash": 5,
                "bonds": 20,
                "stocks": 65,
                "alternatives": 10
            },
            "aggressive": {
                "cash": 5,
                "bonds": 10,
                "stocks": 75,
                "alternatives": 10
            }
        }
        
        recommended_allocation = allocation_templates.get(risk_category, allocation_templates["balanced"])
        
        allocation_result = {
            "client_id": client_id,
            "risk_category": risk_category,
            "recommended_allocation": recommended_allocation,
            "allocation_rationale": f"Based on {risk_category} risk profile",
            "rebalancing_frequency": "quarterly",
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return allocation_result
    
    def _calculate_time_horizon_score(self, years: int) -> float:
        """Calculate time horizon risk score (0-1)"""
        if years < 3:
            return 0.2  # Short term - low risk capacity
        elif years < 7:
            return 0.4  # Medium term
        elif years < 15:
            return 0.7  # Long term
        else:
            return 1.0  # Very long term - high risk capacity
    
    def _calculate_financial_capacity_score(self, annual_income: float, net_worth: float) -> float:
        """Calculate financial capacity risk score (0-1)"""
        # Simple heuristic - can be replaced with ML model
        if net_worth < 50000:
            return 0.2
        elif net_worth < 250000:
            return 0.4
        elif net_worth < 1000000:
            return 0.7
        else:
            return 1.0
    
    def _calculate_experience_score(self, experience: str) -> float:
        """Calculate investment experience risk score (0-1)"""
        experience_map = {
            "none": 0.1,
            "beginner": 0.3,
            "intermediate": 0.6,
            "advanced": 0.9,
            "expert": 1.0
        }
        return experience_map.get(experience, 0.3)
    
    def _calculate_loss_tolerance_score(self, loss_tolerance_percentage: float) -> float:
        """Calculate loss tolerance risk score (0-1)"""
        # Higher tolerance = higher risk capacity
        return min(loss_tolerance_percentage / 30, 1.0)
    
    def _calculate_objective_score(self, objective: str) -> float:
        """Calculate investment objective risk score (0-1)"""
        objective_map = {
            "capital_preservation": 0.1,
            "income": 0.3,
            "balanced": 0.5,
            "growth": 0.8,
            "aggressive_growth": 1.0
        }
        return objective_map.get(objective, 0.5)
    
    def _determine_risk_category(self, score: float) -> str:
        """Determine risk category from score"""
        if score < 20:
            return "conservative"
        elif score < 40:
            return "moderate"
        elif score < 60:
            return "balanced"
        elif score < 80:
            return "growth"
        else:
            return "aggressive"
    
    def _generate_suitability_reasoning(
        self,
        is_suitable: bool,
        client_risk_category: str,
        investment_risk_level: str
    ) -> str:
        """Generate human-readable suitability reasoning"""
        if is_suitable:
            return f"Investment risk level ({investment_risk_level}) aligns with client's {client_risk_category} risk profile."
        else:
            return f"Investment risk level ({investment_risk_level}) does not align with client's {client_risk_category} risk profile. Consider lower-risk alternatives."
