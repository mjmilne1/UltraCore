"""
Client Management AI Agent
Autonomous agent for intelligent client management decisions
Uses ML models and business rules for automation
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio

class AgentDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REVIEW = "review"
    ESCALATE = "escalate"

class ClientManagementAgent:
    """
    Agentic AI for client management
    Capabilities:
    - Risk assessment
    - KYC verification decisions
    - Portfolio recommendations
    - Anomaly detection
    """
    
    def __init__(self):
        self.decision_history = []
        self.confidence_threshold = 0.85
    
    async def assess_client_risk(
        self,
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI-powered risk assessment
        Returns risk score and recommendations
        """
        
        # Extract features
        features = self._extract_risk_features(client_data)
        
        # Calculate risk score (ML model would go here)
        risk_score = self._calculate_risk_score(features)
        
        # Determine risk level
        risk_level = self._get_risk_level(risk_score)
        
        # Generate recommendations
        recommendations = self._generate_risk_recommendations(
            risk_score,
            risk_level,
            features
        )
        
        decision = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": self._calculate_confidence(features),
            "recommendations": recommendations,
            "reasoning": self._explain_risk_assessment(features, risk_score),
            "agent_decision": self._make_risk_decision(risk_score)
        }
        
        self._record_decision("RISK_ASSESSMENT", decision)
        
        return decision
    
    async def verify_kyc_documents(
        self,
        client_id: str,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        AI-powered KYC document verification
        """
        
        verification_results = []
        
        for doc in documents:
            result = await self._verify_document(doc)
            verification_results.append(result)
        
        # Overall decision
        all_verified = all(r["verified"] for r in verification_results)
        confidence = sum(r["confidence"] for r in verification_results) / len(verification_results)
        
        if all_verified and confidence >= self.confidence_threshold:
            decision = AgentDecision.APPROVE
        elif all_verified and confidence >= 0.70:
            decision = AgentDecision.REVIEW
        else:
            decision = AgentDecision.ESCALATE
        
        result = {
            "client_id": client_id,
            "decision": decision,
            "overall_confidence": confidence,
            "documents_verified": verification_results,
            "requires_human_review": decision in [
                AgentDecision.REVIEW,
                AgentDecision.ESCALATE
            ]
        }
        
        self._record_decision("KYC_VERIFICATION", result)
        
        return result
    
    async def recommend_portfolio(
        self,
        client_data: Dict[str, Any],
        risk_profile: str
    ) -> Dict[str, Any]:
        """
        AI-powered portfolio recommendations
        Based on risk profile and client data
        """
        
        from ultracore.services.ultrawealth import australian_etf_universe
        
        # Get appropriate ETFs based on risk profile
        if risk_profile.lower() == "conservative":
            etfs = ["VAF.AX", "VGB.AX", "VAS.AX", "VHY.AX"]
            weights = [0.40, 0.30, 0.20, 0.10]
        elif risk_profile.lower() == "moderate":
            etfs = ["VAS.AX", "VGS.AX", "VAF.AX", "VAP.AX"]
            weights = [0.35, 0.35, 0.20, 0.10]
        elif risk_profile.lower() == "aggressive":
            etfs = ["VGS.AX", "VAS.AX", "NDQ.AX", "VSO.AX"]
            weights = [0.40, 0.30, 0.20, 0.10]
        else:
            etfs = ["VAS.AX", "VGS.AX", "VAF.AX"]
            weights = [0.40, 0.40, 0.20]
        
        # Calculate recommended allocation
        total_value = client_data.get("investment_amount", 100000)
        
        allocations = [
            {
                "ticker": ticker,
                "name": australian_etf_universe.get_etf_info(ticker)["name"],
                "category": australian_etf_universe.get_etf_info(ticker)["category"],
                "weight": weight,
                "amount": total_value * weight
            }
            for ticker, weight in zip(etfs, weights)
        ]
        
        recommendation = {
            "risk_profile": risk_profile,
            "total_investment": total_value,
            "recommended_allocation": allocations,
            "confidence": 0.92,
            "reasoning": self._explain_portfolio_recommendation(
                risk_profile,
                allocations
            ),
            "rebalancing_frequency": self._suggest_rebalancing_frequency(
                risk_profile
            )
        }
        
        self._record_decision("PORTFOLIO_RECOMMENDATION", recommendation)
        
        return recommendation
    
    async def detect_anomalies(
        self,
        client_id: str,
        recent_activity: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect anomalous client behavior
        """
        
        anomalies = []
        
        # Check for unusual patterns
        if len(recent_activity) > 10:
            # High frequency trading
            anomalies.append({
                "type": "high_frequency_trading",
                "severity": "medium",
                "description": "Unusually high trading frequency detected"
            })
        
        # Check for large transactions
        large_transactions = [
            tx for tx in recent_activity
            if tx.get("amount", 0) > 50000
        ]
        
        if large_transactions:
            anomalies.append({
                "type": "large_transaction",
                "severity": "high",
                "description": f"{len(large_transactions)} large transactions detected",
                "transactions": large_transactions
            })
        
        return {
            "client_id": client_id,
            "anomalies_detected": len(anomalies) > 0,
            "anomalies": anomalies,
            "risk_level": "high" if any(a["severity"] == "high" for a in anomalies) else "low",
            "requires_investigation": len(anomalies) > 0
        }
    
    def _extract_risk_features(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features for risk assessment"""
        return {
            "age": self._calculate_age(client_data.get("date_of_birth")),
            "income": client_data.get("annual_income", 0),
            "net_worth": client_data.get("net_worth", 0),
            "investment_experience": client_data.get("investment_experience", "none"),
            "occupation": client_data.get("occupation", "unknown"),
            "has_tfn": client_data.get("tfn_provided", False)
        }
    
    def _calculate_risk_score(self, features: Dict[str, Any]) -> float:
        """
        Calculate risk score (0-100)
        Lower score = lower risk
        """
        score = 50  # Base score
        
        # Age factor
        age = features.get("age", 0)
        if age < 25:
            score += 15
        elif age > 65:
            score += 10
        
        # Income/net worth factor
        income = features.get("income", 0)
        net_worth = features.get("net_worth", 0)
        
        if income < 50000:
            score += 10
        if net_worth < 100000:
            score += 10
        
        # Experience factor
        experience = features.get("investment_experience", "none")
        if experience == "none":
            score += 15
        elif experience == "limited":
            score += 10
        
        # TFN factor
        if not features.get("has_tfn"):
            score += 5
        
        return min(max(score, 0), 100)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level"""
        if risk_score < 30:
            return "low"
        elif risk_score < 60:
            return "medium"
        else:
            return "high"
    
    def _generate_risk_recommendations(
        self,
        risk_score: float,
        risk_level: str,
        features: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.append("Recommend conservative investment strategy")
            recommendations.append("Provide additional client education")
            recommendations.append("Increase monitoring frequency")
        
        if not features.get("has_tfn"):
            recommendations.append("Request TFN for tax optimization")
        
        if features.get("investment_experience") == "none":
            recommendations.append("Schedule financial advisor consultation")
        
        return recommendations
    
    def _explain_risk_assessment(
        self,
        features: Dict[str, Any],
        risk_score: float
    ) -> str:
        """Explain AI reasoning"""
        factors = []
        
        if features.get("age", 0) < 25:
            factors.append("young age")
        if features.get("income", 0) < 50000:
            factors.append("lower income bracket")
        if features.get("investment_experience") == "none":
            factors.append("no investment experience")
        
        if factors:
            return f"Risk score of {risk_score:.1f} based on: {', '.join(factors)}"
        else:
            return f"Risk score of {risk_score:.1f} - profile within normal parameters"
    
    def _make_risk_decision(self, risk_score: float) -> AgentDecision:
        """Make automated decision based on risk"""
        if risk_score < 40:
            return AgentDecision.APPROVE
        elif risk_score < 70:
            return AgentDecision.REVIEW
        else:
            return AgentDecision.ESCALATE
    
    def _calculate_age(self, date_of_birth) -> int:
        """Calculate age from DOB"""
        if not date_of_birth:
            return 0
        from datetime import datetime
        today = datetime.now(timezone.utc)
        return today.year - date_of_birth.year
    
    def _calculate_confidence(self, features: Dict[str, Any]) -> float:
        """Calculate confidence in assessment"""
        # More complete data = higher confidence
        completeness = sum(
            1 for v in features.values()
            if v and v != "unknown" and v != 0
        ) / len(features)
        return round(completeness * 0.9 + 0.1, 2)
    
    async def _verify_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single document (placeholder for ML model)"""
        # In production, this would use computer vision/OCR
        doc_type = document.get("type")
        
        if doc_type in ["passport", "drivers_license", "medicare"]:
            return {
                "document_type": doc_type,
                "verified": True,
                "confidence": 0.95,
                "issues": []
            }
        else:
            return {
                "document_type": doc_type,
                "verified": False,
                "confidence": 0.60,
                "issues": ["Unsupported document type"]
            }
    
    def _explain_portfolio_recommendation(
        self,
        risk_profile: str,
        allocations: List[Dict[str, Any]]
    ) -> str:
        """Explain portfolio recommendation"""
        return (
            f"Based on {risk_profile} risk profile, recommended diversified "
            f"portfolio across {len(allocations)} asset classes for optimal "
            f"risk-adjusted returns."
        )
    
    def _suggest_rebalancing_frequency(self, risk_profile: str) -> str:
        """Suggest rebalancing frequency"""
        if risk_profile.lower() == "conservative":
            return "annually"
        elif risk_profile.lower() == "moderate":
            return "semi-annually"
        else:
            return "quarterly"
    
    def _record_decision(self, decision_type: str, decision: Dict[str, Any]):
        """Record agent decision for audit"""
        self.decision_history.append({
            "type": decision_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision
        })

# Global instance
client_agent = ClientManagementAgent()
