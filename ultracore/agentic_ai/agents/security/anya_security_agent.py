"""
Anya Security Agent
Master security orchestrator with AI-powered threat detection and response
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class FraudAssessment(BaseModel):
    """Fraud detection assessment"""
    is_fraud: bool
    confidence: float  # 0.0 - 1.0
    risk_score: float  # 0.0 - 1.0
    reasons: List[str]
    recommended_action: str  # allow, challenge, block


class AnomalyAssessment(BaseModel):
    """Anomaly detection assessment"""
    is_anomaly: bool
    anomaly_score: float  # 0.0 - 1.0
    deviations: List[str]
    recommended_action: str  # allow, monitor, challenge


class RiskScore(BaseModel):
    """Comprehensive risk score"""
    score: int  # 0-100
    level: str  # low, medium, high, critical
    factors: Dict[str, float]
    recommended_action: str


class ThreatEvent(BaseModel):
    """Security threat event"""
    threat_id: UUID
    threat_type: str
    severity: str  # low, medium, high, critical
    description: str
    indicators: List[str]
    affected_entities: List[UUID]
    detected_at: datetime


class ResponseAction(BaseModel):
    """Automated response action"""
    action_type: str  # block, lock, alert, escalate
    target: str
    reason: str
    executed_at: datetime
    success: bool


class SecurityContext(BaseModel):
    """Security context for decision making"""
    user_id: Optional[UUID] = None
    tenant_id: UUID
    ip_address: str
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    user_agent: Optional[str] = None
    timestamp: datetime


# ============================================================================
# Anya Security Agent
# ============================================================================

class AnyaSecurityAgent:
    """
    Anya Security Agent
    
    Master security orchestrator with AI-powered capabilities:
    - Real-time fraud detection
    - Behavioral anomaly detection
    - Comprehensive risk scoring
    - Automated threat response
    - Adaptive security controls (RL)
    """
    
    def __init__(self):
        self.name = "Anya Security"
        self.version = "1.0.0"
        self.capabilities = [
            "fraud_detection",
            "anomaly_detection",
            "risk_scoring",
            "threat_intelligence",
            "incident_response",
            "adaptive_controls"
        ]
        
        # ML models (would be loaded from saved models in production)
        self.fraud_model = None
        self.anomaly_model = None
        self.risk_model = None
        
        # RL agents
        self.access_control_agent = None
        self.rate_limit_agent = None
        
        # Threat intelligence cache
        self.threat_intelligence = {}
        
        logger.info(f"✓ {self.name} initialized with {len(self.capabilities)} capabilities")
    
    # ========================================================================
    # Fraud Detection
    # ========================================================================
    
    async def detect_fraud(
        self,
        transaction: Dict[str, Any],
        context: SecurityContext
    ) -> FraudAssessment:
        """
        Real-time fraud detection using ML
        
        Analyzes:
        - Transaction patterns
        - User behavior
        - Device fingerprints
        - Geolocation anomalies
        - Velocity checks
        
        Returns:
            FraudAssessment with fraud probability and recommended action
        """
        logger.info(f"Analyzing transaction for fraud: {transaction.get('transaction_id')}")
        
        # Extract features
        features = await self._extract_fraud_features(transaction, context)
        
        # ML model prediction
        fraud_score = await self._predict_fraud(features)
        
        # Determine if fraud
        is_fraud = fraud_score > 0.8
        
        # Identify reasons
        reasons = await self._identify_fraud_reasons(features, fraud_score)
        
        # Recommend action
        if fraud_score > 0.9:
            action = "block"
        elif fraud_score > 0.7:
            action = "challenge"
        else:
            action = "allow"
        
        assessment = FraudAssessment(
            is_fraud=is_fraud,
            confidence=fraud_score,
            risk_score=fraud_score,
            reasons=reasons,
            recommended_action=action
        )
        
        logger.info(f"Fraud assessment: {action} (score={fraud_score:.2f})")
        
        return assessment
    
    async def _extract_fraud_features(
        self,
        transaction: Dict[str, Any],
        context: SecurityContext
    ) -> Dict[str, float]:
        """Extract features for fraud detection model"""
        
        # Normalize transaction amount
        amount = float(transaction.get("amount", 0))
        amount_normalized = min(amount / 10000, 1.0)  # Cap at $10k
        
        # Time features
        hour = context.timestamp.hour
        is_night = 1.0 if (hour < 6 or hour > 22) else 0.0
        is_weekend = 1.0 if context.timestamp.weekday() >= 5 else 0.0
        
        # Geolocation features
        geo = context.geolocation or {}
        unusual_location = await self._check_unusual_location(
            context.user_id,
            geo.get("latitude"),
            geo.get("longitude")
        )
        
        # Device features
        new_device = await self._check_new_device(
            context.user_id,
            context.device_fingerprint
        )
        
        # Velocity features
        velocity_score = await self._calculate_velocity(
            context.user_id,
            context.timestamp
        )
        
        features = {
            "amount_normalized": amount_normalized,
            "is_night": is_night,
            "is_weekend": is_weekend,
            "unusual_location": unusual_location,
            "new_device": new_device,
            "velocity_score": velocity_score,
        }
        
        return features
    
    async def _predict_fraud(self, features: Dict[str, float]) -> float:
        """
        Predict fraud probability using ML model
        
        In production, this would use a trained XGBoost model
        For now, use a simple heuristic
        """
        # Weighted score
        score = (
            features["amount_normalized"] * 0.3 +
            features["is_night"] * 0.1 +
            features["is_weekend"] * 0.05 +
            features["unusual_location"] * 0.25 +
            features["new_device"] * 0.15 +
            features["velocity_score"] * 0.15
        )
        
        return min(score, 1.0)
    
    async def _identify_fraud_reasons(
        self,
        features: Dict[str, float],
        fraud_score: float
    ) -> List[str]:
        """Identify specific fraud indicators"""
        reasons = []
        
        if features["unusual_location"] > 0.5:
            reasons.append("unusual_location")
        
        if features["new_device"] > 0.5:
            reasons.append("new_device")
        
        if features["velocity_score"] > 0.7:
            reasons.append("high_velocity")
        
        if features["is_night"] > 0.5:
            reasons.append("unusual_time")
        
        if features["amount_normalized"] > 0.8:
            reasons.append("high_amount")
        
        return reasons
    
    # ========================================================================
    # Anomaly Detection
    # ========================================================================
    
    async def detect_anomaly(
        self,
        event: Dict[str, Any],
        context: SecurityContext
    ) -> AnomalyAssessment:
        """
        Behavioral anomaly detection using ML
        
        Analyzes:
        - Login patterns
        - API usage patterns
        - Data access patterns
        - Time-based anomalies
        
        Returns:
            AnomalyAssessment with anomaly score and recommended action
        """
        logger.info(f"Analyzing event for anomalies: {event.get('event_type')}")
        
        # Extract behavior features
        features = await self._extract_anomaly_features(event, context)
        
        # ML model prediction (Isolation Forest)
        anomaly_score = await self._predict_anomaly(features)
        
        # Determine if anomaly
        is_anomaly = anomaly_score > 0.9
        
        # Identify deviations
        deviations = await self._identify_deviations(features, anomaly_score)
        
        # Recommend action
        if anomaly_score > 0.95:
            action = "challenge"
        elif anomaly_score > 0.85:
            action = "monitor"
        else:
            action = "allow"
        
        assessment = AnomalyAssessment(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            deviations=deviations,
            recommended_action=action
        )
        
        logger.info(f"Anomaly assessment: {action} (score={anomaly_score:.2f})")
        
        return assessment
    
    async def _extract_anomaly_features(
        self,
        event: Dict[str, Any],
        context: SecurityContext
    ) -> Dict[str, float]:
        """Extract features for anomaly detection"""
        
        # Time-based features
        hour = context.timestamp.hour
        usual_hours = await self._get_usual_login_hours(context.user_id)
        time_deviation = abs(hour - usual_hours) / 24.0
        
        # Location-based features
        geo = context.geolocation or {}
        location_deviation = await self._calculate_location_deviation(
            context.user_id,
            geo.get("latitude"),
            geo.get("longitude")
        )
        
        # Device-based features
        device_trust = await self._get_device_trust_score(
            context.device_fingerprint
        )
        
        features = {
            "time_deviation": time_deviation,
            "location_deviation": location_deviation,
            "device_trust": 1.0 - device_trust,  # Invert (higher = more anomalous)
        }
        
        return features
    
    async def _predict_anomaly(self, features: Dict[str, float]) -> float:
        """
        Predict anomaly score using ML model
        
        In production, this would use Isolation Forest
        For now, use a simple heuristic
        """
        # Weighted score
        score = (
            features["time_deviation"] * 0.3 +
            features["location_deviation"] * 0.4 +
            features["device_trust"] * 0.3
        )
        
        return min(score, 1.0)
    
    async def _identify_deviations(
        self,
        features: Dict[str, float],
        anomaly_score: float
    ) -> List[str]:
        """Identify specific anomalies"""
        deviations = []
        
        if features["time_deviation"] > 0.5:
            deviations.append("unusual_time")
        
        if features["location_deviation"] > 0.5:
            deviations.append("unusual_location")
        
        if features["device_trust"] > 0.5:
            deviations.append("untrusted_device")
        
        return deviations
    
    # ========================================================================
    # Risk Scoring
    # ========================================================================
    
    async def assess_risk(self, context: SecurityContext) -> RiskScore:
        """
        Comprehensive risk assessment
        
        Combines multiple signals:
        - Fraud detection score
        - Anomaly detection score
        - User trust score
        - Device trust score
        - Geolocation risk
        - Threat intelligence
        
        Returns:
            RiskScore (0-100) with risk level and recommended action
        """
        logger.info(f"Assessing risk for user: {context.user_id}")
        
        # Get individual risk factors
        fraud_risk = await self._get_fraud_risk(context)
        anomaly_risk = await self._get_anomaly_risk(context)
        user_trust = await self._get_user_trust_score(context.user_id)
        device_trust = await self._get_device_trust_score(context.device_fingerprint)
        geo_risk = await self._get_geolocation_risk(context.geolocation)
        threat_intel = await self._check_threat_intelligence(context.ip_address)
        
        # Calculate weighted risk score
        risk_score = int(
            fraud_risk * 25 +
            anomaly_risk * 20 +
            (1.0 - user_trust) * 20 +
            (1.0 - device_trust) * 15 +
            geo_risk * 10 +
            threat_intel * 10
        )
        
        # Determine risk level
        if risk_score >= 90:
            level = "critical"
            action = "deny"
        elif risk_score >= 70:
            level = "high"
            action = "challenge"
        elif risk_score >= 40:
            level = "medium"
            action = "monitor"
        else:
            level = "low"
            action = "allow"
        
        factors = {
            "fraud_risk": fraud_risk,
            "anomaly_risk": anomaly_risk,
            "user_trust": user_trust,
            "device_trust": device_trust,
            "geo_risk": geo_risk,
            "threat_intel": threat_intel,
        }
        
        risk = RiskScore(
            score=risk_score,
            level=level,
            factors=factors,
            recommended_action=action
        )
        
        logger.info(f"Risk assessment: {level} (score={risk_score})")
        
        return risk
    
    # ========================================================================
    # Threat Response
    # ========================================================================
    
    async def respond_to_threat(self, threat: ThreatEvent) -> ResponseAction:
        """
        Automated threat response
        
        Actions based on severity:
        - Low: Log + Monitor
        - Medium: Alert + Restrict
        - High: Block + Lock + Alert
        - Critical: Block + Lock + Alert + Escalate
        
        Returns:
            ResponseAction with details of action taken
        """
        logger.warning(f"Responding to threat: {threat.threat_type} (severity={threat.severity})")
        
        if threat.severity == "critical":
            action = await self._execute_critical_response(threat)
        elif threat.severity == "high":
            action = await self._execute_high_response(threat)
        elif threat.severity == "medium":
            action = await self._execute_medium_response(threat)
        else:
            action = await self._execute_low_response(threat)
        
        logger.info(f"Threat response executed: {action.action_type}")
        
        return action
    
    async def _execute_critical_response(self, threat: ThreatEvent) -> ResponseAction:
        """Execute critical threat response"""
        # Block + Lock + Alert + Escalate
        await self._block_entities(threat.affected_entities)
        await self._lock_accounts(threat.affected_entities)
        await self._send_security_alert(threat, priority="critical")
        await self._escalate_to_security_team(threat)
        
        return ResponseAction(
            action_type="block_lock_alert_escalate",
            target=str(threat.affected_entities),
            reason=threat.description,
            executed_at=datetime.utcnow(),
            success=True
        )
    
    async def _execute_high_response(self, threat: ThreatEvent) -> ResponseAction:
        """Execute high severity response"""
        # Block + Lock + Alert
        await self._block_entities(threat.affected_entities)
        await self._lock_accounts(threat.affected_entities)
        await self._send_security_alert(threat, priority="high")
        
        return ResponseAction(
            action_type="block_lock_alert",
            target=str(threat.affected_entities),
            reason=threat.description,
            executed_at=datetime.utcnow(),
            success=True
        )
    
    async def _execute_medium_response(self, threat: ThreatEvent) -> ResponseAction:
        """Execute medium severity response"""
        # Alert + Restrict
        await self._send_security_alert(threat, priority="medium")
        await self._restrict_access(threat.affected_entities)
        
        return ResponseAction(
            action_type="alert_restrict",
            target=str(threat.affected_entities),
            reason=threat.description,
            executed_at=datetime.utcnow(),
            success=True
        )
    
    async def _execute_low_response(self, threat: ThreatEvent) -> ResponseAction:
        """Execute low severity response"""
        # Log + Monitor
        await self._log_threat(threat)
        await self._enable_monitoring(threat.affected_entities)
        
        return ResponseAction(
            action_type="log_monitor",
            target=str(threat.affected_entities),
            reason=threat.description,
            executed_at=datetime.utcnow(),
            success=True
        )
    
    # ========================================================================
    # Helper Methods (Simulated - would integrate with real systems)
    # ========================================================================
    
    async def _check_unusual_location(self, user_id: Optional[UUID], lat: Optional[float], lon: Optional[float]) -> float:
        """Check if location is unusual for user"""
        # Simulated - would check against user's location history
        return 0.0
    
    async def _check_new_device(self, user_id: Optional[UUID], device_fingerprint: Optional[str]) -> float:
        """Check if device is new for user"""
        # Simulated - would check against user's device history
        return 0.0
    
    async def _calculate_velocity(self, user_id: Optional[UUID], timestamp: datetime) -> float:
        """Calculate transaction velocity"""
        # Simulated - would count recent transactions
        return 0.0
    
    async def _get_usual_login_hours(self, user_id: Optional[UUID]) -> float:
        """Get user's usual login hours"""
        # Simulated - would analyze login history
        return 12.0  # Noon
    
    async def _calculate_location_deviation(self, user_id: Optional[UUID], lat: Optional[float], lon: Optional[float]) -> float:
        """Calculate location deviation from usual"""
        # Simulated - would calculate distance from usual locations
        return 0.0
    
    async def _get_device_trust_score(self, device_fingerprint: Optional[str]) -> float:
        """Get device trust score"""
        # Simulated - would check device reputation
        return 0.8
    
    async def _get_fraud_risk(self, context: SecurityContext) -> float:
        """Get fraud risk score"""
        return 0.0
    
    async def _get_anomaly_risk(self, context: SecurityContext) -> float:
        """Get anomaly risk score"""
        return 0.0
    
    async def _get_user_trust_score(self, user_id: Optional[UUID]) -> float:
        """Get user trust score"""
        return 0.9
    
    async def _get_geolocation_risk(self, geolocation: Optional[Dict[str, Any]]) -> float:
        """Get geolocation risk score"""
        return 0.0
    
    async def _check_threat_intelligence(self, ip_address: str) -> float:
        """Check IP against threat intelligence"""
        return 0.0
    
    async def _block_entities(self, entities: List[UUID]):
        """Block entities"""
        logger.info(f"Blocking entities: {entities}")
    
    async def _lock_accounts(self, entities: List[UUID]):
        """Lock accounts"""
        logger.info(f"Locking accounts: {entities}")
    
    async def _send_security_alert(self, threat: ThreatEvent, priority: str):
        """Send security alert"""
        logger.warning(f"Security alert [{priority}]: {threat.description}")
    
    async def _escalate_to_security_team(self, threat: ThreatEvent):
        """Escalate to security team"""
        logger.critical(f"Escalating to security team: {threat.description}")
    
    async def _restrict_access(self, entities: List[UUID]):
        """Restrict access"""
        logger.info(f"Restricting access for entities: {entities}")
    
    async def _log_threat(self, threat: ThreatEvent):
        """Log threat"""
        logger.info(f"Logging threat: {threat.description}")
    
    async def _enable_monitoring(self, entities: List[UUID]):
        """Enable enhanced monitoring"""
        logger.info(f"Enabling monitoring for entities: {entities}")


# ============================================================================
# Convenience function
# ============================================================================

def get_security_agent() -> AnyaSecurityAgent:
    """Get singleton security agent instance"""
    return AnyaSecurityAgent()
