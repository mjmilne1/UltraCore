"""
Agentic AI for Cash Management
Fraud detection, validation, and intelligent monitoring
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import random

class FraudRiskLevel(str, Enum):
    """Fraud risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentAction(str, Enum):
    """Agent actions"""
    APPROVE = "approve"
    REVIEW = "review"
    BLOCK = "block"
    REQUEST_VERIFICATION = "request_verification"

class CashFraudDetectorAgent:
    """
    Agentic AI Fraud Detector
    
    Uses AI agents to:
    - Detect fraudulent transactions
    - Validate transaction patterns
    - Monitor anomalies
    - Make intelligent decisions
    - Learn from feedback
    """
    
    def __init__(self):
        self.fraud_cases = []
        self.learning_history = []
        self.detection_rules = self._initialize_rules()
        
    def _initialize_rules(self) -> List[Dict[str, Any]]:
        """Initialize fraud detection rules"""
        
        return [
            {
                "rule_id": "RULE-001",
                "name": "Large withdrawal",
                "condition": lambda tx: tx.get("amount", 0) > 50000,
                "risk_score": 30,
                "action": AgentAction.REVIEW
            },
            {
                "rule_id": "RULE-002",
                "name": "Multiple withdrawals same day",
                "condition": lambda tx: True,  # Would check history
                "risk_score": 25,
                "action": AgentAction.REVIEW
            },
            {
                "rule_id": "RULE-003",
                "name": "Unusual withdrawal time",
                "condition": lambda tx: datetime.fromisoformat(tx.get("timestamp", datetime.now(timezone.utc).isoformat())).hour < 6,
                "risk_score": 15,
                "action": AgentAction.REVIEW
            },
            {
                "rule_id": "RULE-004",
                "name": "New destination account",
                "condition": lambda tx: True,  # Would check history
                "risk_score": 20,
                "action": AgentAction.REVIEW
            },
            {
                "rule_id": "RULE-005",
                "name": "Rapid succession transactions",
                "condition": lambda tx: True,  # Would check timing
                "risk_score": 35,
                "action": AgentAction.BLOCK
            }
        ]
    
    def analyze_transaction(
        self,
        transaction: Dict[str, Any],
        account_history: List[Dict[str, Any]],
        client_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze transaction for fraud using AI agent
        
        Agent considers:
        - Transaction amount
        - Transaction pattern
        - Historical behavior
        - Client risk profile
        - Time and location
        - Behavioral anomalies
        """
        
        fraud_indicators = []
        risk_score = 0
        recommended_action = AgentAction.APPROVE
        
        # Run detection rules
        for rule in self.detection_rules:
            if rule["condition"](transaction):
                fraud_indicators.append({
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["name"],
                    "risk_contribution": rule["risk_score"]
                })
                risk_score += rule["risk_score"]
        
        # Behavioral analysis
        behavioral_risk = self._analyze_behavior(
            transaction,
            account_history,
            client_profile
        )
        
        risk_score += behavioral_risk["risk_score"]
        fraud_indicators.extend(behavioral_risk["indicators"])
        
        # Pattern recognition
        pattern_risk = self._detect_patterns(transaction, account_history)
        risk_score += pattern_risk["risk_score"]
        fraud_indicators.extend(pattern_risk["indicators"])
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = FraudRiskLevel.CRITICAL
            recommended_action = AgentAction.BLOCK
        elif risk_score >= 60:
            risk_level = FraudRiskLevel.HIGH
            recommended_action = AgentAction.REQUEST_VERIFICATION
        elif risk_score >= 40:
            risk_level = FraudRiskLevel.MEDIUM
            recommended_action = AgentAction.REVIEW
        else:
            risk_level = FraudRiskLevel.LOW
            recommended_action = AgentAction.APPROVE
        
        analysis = {
            "transaction_id": transaction.get("transaction_id"),
            "fraud_score": min(100, risk_score),
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "fraud_indicators": fraud_indicators,
            "agent_confidence": self._calculate_confidence(risk_score, len(fraud_indicators)),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "agent_reasoning": self._generate_reasoning(fraud_indicators, risk_score)
        }
        
        # Record for learning
        self.fraud_cases.append(analysis)
        
        return analysis
    
    def _analyze_behavior(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns"""
        
        indicators = []
        risk_score = 0
        
        amount = transaction.get("amount", 0)
        
        # Check if amount unusual for client
        if history:
            avg_amount = sum(h.get("amount", 0) for h in history) / len(history)
            
            if amount > avg_amount * 5:
                indicators.append({
                    "rule_id": "BEH-001",
                    "rule_name": "Amount 5x higher than average",
                    "risk_contribution": 25
                })
                risk_score += 25
        
        # Check transaction frequency
        if len(history) > 10:
            recent_24h = [
                h for h in history
                if (datetime.now(timezone.utc) - datetime.fromisoformat(h.get("timestamp", datetime.now(timezone.utc).isoformat()))).days < 1
            ]
            
            if len(recent_24h) > 5:
                indicators.append({
                    "rule_id": "BEH-002",
                    "rule_name": "Unusually high frequency (>5 in 24h)",
                    "risk_contribution": 20
                })
                risk_score += 20
        
        # Check client risk profile
        client_risk = profile.get("risk_rating", "low")
        if client_risk in ["high", "extreme"]:
            indicators.append({
                "rule_id": "BEH-003",
                "rule_name": "High-risk client profile",
                "risk_contribution": 15
            })
            risk_score += 15
        
        return {
            "risk_score": risk_score,
            "indicators": indicators
        }
    
    def _detect_patterns(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect fraud patterns"""
        
        indicators = []
        risk_score = 0
        
        # Structuring pattern (multiple transactions just under threshold)
        amount = transaction.get("amount", 0)
        
        if 9000 <= amount < 10000:
            similar_amounts = [
                h for h in history
                if 9000 <= h.get("amount", 0) < 10000
                and (datetime.now(timezone.utc) - datetime.fromisoformat(h.get("timestamp", datetime.now(timezone.utc).isoformat()))).days < 7
            ]
            
            if len(similar_amounts) >= 2:
                indicators.append({
                    "rule_id": "PAT-001",
                    "rule_name": "Structuring pattern detected",
                    "risk_contribution": 40
                })
                risk_score += 40
        
        # Rapid escalation pattern
        if len(history) >= 5:
            recent = sorted(history[-5:], key=lambda x: x.get("timestamp", ""))
            amounts = [r.get("amount", 0) for r in recent]
            
            escalating = all(amounts[i] < amounts[i+1] for i in range(len(amounts)-1))
            
            if escalating and amount > amounts[-1] * 2:
                indicators.append({
                    "rule_id": "PAT-002",
                    "rule_name": "Rapid escalation pattern",
                    "risk_contribution": 30
                })
                risk_score += 30
        
        return {
            "risk_score": risk_score,
            "indicators": indicators
        }
    
    def _calculate_confidence(self, risk_score: float, indicator_count: int) -> float:
        """Calculate agent confidence in assessment"""
        
        # More indicators = higher confidence
        # Higher risk score with many indicators = higher confidence
        
        if indicator_count == 0:
            return 0.95  # High confidence it's safe
        
        confidence = min(0.95, 0.5 + (indicator_count * 0.1) + (risk_score / 200))
        
        return confidence
    
    def _generate_reasoning(
        self,
        indicators: List[Dict[str, Any]],
        risk_score: float
    ) -> str:
        """Generate human-readable reasoning"""
        
        if not indicators:
            return "Transaction appears normal with no fraud indicators."
        
        reasoning = f"Transaction flagged with {len(indicators)} fraud indicators (risk score: {risk_score:.0f}/100). "
        
        top_indicators = sorted(indicators, key=lambda x: x["risk_contribution"], reverse=True)[:3]
        
        reasoning += "Primary concerns: "
        reasoning += ", ".join([ind["rule_name"] for ind in top_indicators])
        reasoning += ". Recommend manual review or additional verification."
        
        return reasoning
    
    def learn_from_feedback(
        self,
        transaction_id: str,
        actual_fraud: bool,
        notes: str = ""
    ):
        """Learn from feedback to improve detection"""
        
        # Find original analysis
        original = next(
            (case for case in self.fraud_cases if case["transaction_id"] == transaction_id),
            None
        )
        
        if original:
            learning_record = {
                "transaction_id": transaction_id,
                "predicted_fraud": original["risk_level"] in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL],
                "actual_fraud": actual_fraud,
                "correct_prediction": (original["risk_level"] in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]) == actual_fraud,
                "original_score": original["fraud_score"],
                "notes": notes,
                "learned_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.learning_history.append(learning_record)
            
            # Adjust rules based on feedback (simplified RL approach)
            if not learning_record["correct_prediction"]:
                self._adjust_rules(original, actual_fraud)
    
    def _adjust_rules(self, analysis: Dict[str, Any], actual_fraud: bool):
        """Adjust rules based on feedback"""
        
        # If false positive (predicted fraud but wasn't)
        if not actual_fraud and analysis["risk_level"] in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
            # Reduce risk scores of triggered rules
            for indicator in analysis["fraud_indicators"]:
                rule_id = indicator.get("rule_id")
                for rule in self.detection_rules:
                    if rule["rule_id"] == rule_id:
                        rule["risk_score"] = max(5, rule["risk_score"] - 2)
        
        # If false negative (didn't predict fraud but was)
        elif actual_fraud and analysis["risk_level"] not in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
            # Increase risk scores of triggered rules
            for indicator in analysis["fraud_indicators"]:
                rule_id = indicator.get("rule_id")
                for rule in self.detection_rules:
                    if rule["rule_id"] == rule_id:
                        rule["risk_score"] = min(50, rule["risk_score"] + 3)
    
    def get_agent_performance(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        
        if not self.learning_history:
            return {
                "total_predictions": 0,
                "accuracy": 0,
                "precision": 0,
                "recall": 0
            }
        
        total = len(self.learning_history)
        correct = sum(1 for l in self.learning_history if l["correct_prediction"])
        
        true_positives = sum(
            1 for l in self.learning_history
            if l["predicted_fraud"] and l["actual_fraud"]
        )
        
        false_positives = sum(
            1 for l in self.learning_history
            if l["predicted_fraud"] and not l["actual_fraud"]
        )
        
        false_negatives = sum(
            1 for l in self.learning_history
            if not l["predicted_fraud"] and l["actual_fraud"]
        )
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        
        return {
            "total_predictions": total,
            "accuracy": (correct / total) * 100 if total > 0 else 0,
            "precision": precision * 100,
            "recall": recall * 100,
            "f1_score": (2 * precision * recall) / (precision + recall) * 100 if (precision + recall) > 0 else 0
        }

# Global fraud detector agent
fraud_detector_agent = CashFraudDetectorAgent()
