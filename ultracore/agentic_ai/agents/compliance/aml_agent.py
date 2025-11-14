"""
AML Monitoring AI Agent
Autonomous transaction monitoring and suspicious activity detection
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AMLMonitoringAgent:
    """
    Autonomous AI agent for AML/CTF compliance monitoring
    
    Capabilities:
    - Real-time transaction monitoring
    - Pattern detection (ML-powered)
    - Automatic risk scoring
    - SMR filing recommendations
    """
    
    def __init__(self):
        self.name = "AML_Monitor"
        self.version = "1.0"
        
        # AML rules (enhanced with ML in production)
        self.rules = {
            "large_transaction": {"threshold": 10000, "score": 20},
            "very_large_transaction": {"threshold": 50000, "score": 30},
            "rapid_succession": {"count": 10, "hours": 24, "score": 25},
            "high_frequency_withdrawals": {"count": 5, "days": 7, "score": 15},
            "round_number_structuring": {"score": 10},
            "high_daily_volume": {"threshold": 50000, "score": 25}
        }
        
        self.suspicious_threshold = 70
    
    def monitor_transaction(
        self,
        transaction_id: str,
        user_id: str,
        transaction_type: str,
        amount: float,
        currency: str,
        user_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Monitor transaction for suspicious activity
        
        Returns:
            Dict with risk_score, triggered_rules, is_suspicious, recommendation
        """
        risk_score = 0
        triggered_rules = []
        
        # Rule 1: Large transaction
        if amount >= self.rules["large_transaction"]["threshold"]:
            risk_score += self.rules["large_transaction"]["score"]
            triggered_rules.append("large_transaction")
        
        # Rule 2: Very large transaction
        if amount >= self.rules["very_large_transaction"]["threshold"]:
            risk_score += self.rules["very_large_transaction"]["score"]
            triggered_rules.append("very_large_transaction")
        
        # Rule 3: Rapid succession
        recent_txns = [
            t for t in user_history
            if (datetime.utcnow() - datetime.fromisoformat(t["timestamp"])).total_seconds() < 86400
        ]
        if len(recent_txns) > self.rules["rapid_succession"]["count"]:
            risk_score += self.rules["rapid_succession"]["score"]
            triggered_rules.append("rapid_succession")
        
        # Rule 4: High frequency withdrawals
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_withdrawals = [
            t for t in user_history
            if t["type"] == "withdrawal" and datetime.fromisoformat(t["timestamp"]) > week_ago
        ]
        if len(recent_withdrawals) > self.rules["high_frequency_withdrawals"]["count"]:
            risk_score += self.rules["high_frequency_withdrawals"]["score"]
            triggered_rules.append("high_frequency_withdrawals")
        
        # Rule 5: Round number structuring
        if amount % 1000 == 0 and amount >= 5000:
            risk_score += self.rules["round_number_structuring"]["score"]
            triggered_rules.append("round_number_structuring")
        
        # Rule 6: High daily volume
        today_txns = [
            t for t in user_history
            if datetime.fromisoformat(t["timestamp"]).date() == datetime.utcnow().date()
        ]
        daily_volume = sum(t["amount"] for t in today_txns) + amount
        if daily_volume > self.rules["high_daily_volume"]["threshold"]:
            risk_score += self.rules["high_daily_volume"]["score"]
            triggered_rules.append("high_daily_volume")
        
        # Determine if suspicious
        is_suspicious = risk_score >= self.suspicious_threshold
        
        # AI recommendation
        recommendation = self._generate_recommendation(
            risk_score,
            triggered_rules,
            is_suspicious
        )
        
        logger.info(
            f"AML Monitor: Transaction {transaction_id} - "
            f"Risk Score: {risk_score}, Suspicious: {is_suspicious}"
        )
        
        return {
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "triggered_rules": triggered_rules,
            "is_suspicious": is_suspicious,
            "requires_smr": is_suspicious and risk_score >= 80,
            "recommendation": recommendation,
            "monitored_by": self.name,
            "monitored_at": datetime.utcnow().isoformat()
        }
    
    def _generate_recommendation(
        self,
        risk_score: int,
        triggered_rules: List[str],
        is_suspicious: bool
    ) -> str:
        """Generate AI recommendation based on analysis"""
        if risk_score >= 90:
            return "IMMEDIATE_ACTION: File SMR with AUSTRAC and freeze account pending investigation"
        elif risk_score >= 80:
            return "HIGH_PRIORITY: File SMR with AUSTRAC within 24 hours"
        elif is_suspicious:
            return "REVIEW_REQUIRED: Manual review by compliance officer recommended"
        elif risk_score >= 50:
            return "MONITOR: Continue monitoring for pattern development"
        else:
            return "NORMAL: No action required"
    
    def assess_customer_risk(
        self,
        customer_data: Dict[str, Any],
        transaction_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Assess overall customer risk level
        Uses ML model in production
        """
        risk_factors = []
        risk_score = 0
        
        # Factor 1: Transaction volume
        total_volume = sum(t["amount"] for t in transaction_history)
        if total_volume > 100000:
            risk_score += 20
            risk_factors.append("high_transaction_volume")
        
        # Factor 2: High-risk jurisdiction
        if customer_data.get("country") in ["Unknown", "High-Risk"]:
            risk_score += 30
            risk_factors.append("high_risk_jurisdiction")
        
        # Factor 3: PEP status
        if customer_data.get("is_pep"):
            risk_score += 25
            risk_factors.append("politically_exposed_person")
        
        # Factor 4: Sanctions list
        if customer_data.get("on_sanctions_list"):
            risk_score += 50
            risk_factors.append("sanctions_list_match")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "very_high"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "enhanced_due_diligence_required": risk_score >= 50,
            "assessed_by": self.name,
            "assessed_at": datetime.utcnow().isoformat()
        }
