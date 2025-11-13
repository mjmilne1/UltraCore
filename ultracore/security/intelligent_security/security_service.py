"""
Intelligent Security Service

Main service integrating ML/RL models with event sourcing.
"""

from typing import Dict, Optional
from datetime import datetime
import asyncio

from ultracore.ml.security import (
    FraudDetectionModel,
    TransactionFeatures,
    AnomalyDetectionModel,
    BehaviorFeatures,
    AdaptiveAccessControlAgent,
    AccessState,
    AdaptiveRateLimitAgent,
    TrafficState
)
from .event_producer import SecurityEventProducer


class IntelligentSecurityService:
    """
    Intelligent security service with AI/ML capabilities.
    
    Provides:
    - Real-time fraud detection
    - Behavioral anomaly detection
    - Adaptive access control
    - Dynamic rate limiting
    - Event sourcing for all security events
    """
    
    def __init__(self, event_producer: Optional[SecurityEventProducer] = None):
        # ML/RL Models
        self.fraud_model = FraudDetectionModel()
        self.anomaly_model = AnomalyDetectionModel()
        self.access_control_agent = AdaptiveAccessControlAgent()
        self.rate_limit_agent = AdaptiveRateLimitAgent()
        
        # Event producer
        self.event_producer = event_producer or SecurityEventProducer()
    
    async def detect_fraud(
        self,
        tenant_id: str,
        transaction_id: str,
        amount: float,
        timestamp: datetime,
        user_id: str,
        user_history: Dict,
        device_info: Dict,
        location_info: Dict
    ) -> Dict:
        """
        Detect fraud in transaction.
        
        Returns:
            Decision dict with fraud_score, decision, and risk_factors
        """
        # Extract features
        features = self.fraud_model.extract_features(
            amount=amount,
            timestamp=timestamp,
            user_history=user_history,
            device_info=device_info,
            location_info=location_info
        )
        
        # Predict fraud
        fraud_score, details = self.fraud_model.predict(features)
        
        # Make decision
        if fraud_score > 0.8:
            decision = "deny"
        elif fraud_score > 0.5:
            decision = "review"
        else:
            decision = "allow"
        
        # Publish event
        await self.event_producer.publish_fraud_detection(
            tenant_id=tenant_id,
            transaction_id=transaction_id,
            fraud_score=fraud_score,
            risk_factors=details.get("high_risk_factors", []),
            decision=decision,
            amount=amount,
            user_id=user_id,
            metadata={
                "details": details,
                "features": features.__dict__
            }
        )
        
        return {
            "fraud_score": fraud_score,
            "decision": decision,
            "risk_factors": details.get("high_risk_factors", []),
            "details": details
        }
    
    async def detect_anomaly(
        self,
        tenant_id: str,
        session_id: str,
        user_id: str,
        login_hour: int,
        login_day_of_week: int,
        api_calls_per_minute: float,
        unique_endpoints_accessed: int,
        data_volume_mb: float,
        failed_attempts: int,
        session_duration_minutes: float,
        ip_reputation_score: float,
        device_fingerprint_match: bool,
        location_match: bool
    ) -> Dict:
        """
        Detect behavioral anomalies.
        
        Returns:
            Decision dict with anomaly_score, action, and indicators
        """
        # Create features
        features = BehaviorFeatures(
            login_hour=login_hour,
            login_day_of_week=login_day_of_week,
            api_calls_per_minute=api_calls_per_minute,
            unique_endpoints_accessed=unique_endpoints_accessed,
            data_volume_mb=data_volume_mb,
            failed_attempts=failed_attempts,
            session_duration_minutes=session_duration_minutes,
            ip_reputation_score=ip_reputation_score,
            device_fingerprint_match=device_fingerprint_match,
            location_match=location_match
        )
        
        # Predict anomaly
        anomaly_score, details = self.anomaly_model.predict(features, user_id)
        
        # Update baseline
        self.anomaly_model.update_baseline(user_id, features)
        
        # Determine action
        if anomaly_score > 0.8:
            action = "block"
        elif anomaly_score > 0.6:
            action = "alert"
        else:
            action = "monitor"
        
        # Publish event
        await self.event_producer.publish_anomaly_detection(
            tenant_id=tenant_id,
            session_id=session_id,
            anomaly_score=anomaly_score,
            anomaly_indicators=details.get("anomaly_indicators", []),
            action_taken=action,
            user_id=user_id,
            metadata={
                "details": details,
                "features": features.__dict__
            }
        )
        
        return {
            "anomaly_score": anomaly_score,
            "action": action,
            "indicators": details.get("anomaly_indicators", []),
            "details": details
        }
    
    async def check_access(
        self,
        tenant_id: str,
        user_id: str,
        resource_id: str,
        resource_type: str,
        action_requested: str,
        user_risk_score: float,
        resource_sensitivity: int,
        time_of_day: int,
        recent_violations: int,
        authentication_strength: int,
        location_trust: float,
        device_trust: float
    ) -> Dict:
        """
        Check access control with RL agent.
        
        Returns:
            Decision dict with action, confidence, and reasoning
        """
        # Get decision from RL agent
        decision = self.access_control_agent.decide_access(
            user_risk_score=user_risk_score,
            resource_sensitivity=resource_sensitivity,
            time_of_day=time_of_day,
            recent_violations=recent_violations,
            authentication_strength=authentication_strength,
            location_trust=location_trust,
            device_trust=device_trust,
            training=False  # Production mode
        )
        
        # Publish event
        await self.event_producer.publish_access_control(
            tenant_id=tenant_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action_requested=action_requested,
            decision=decision["action"],
            risk_score=user_risk_score,
            reasoning=decision["reasoning"],
            user_id=user_id,
            metadata={
                "confidence": decision["confidence"],
                "q_values": decision["q_values"]
            }
        )
        
        return decision
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        user_id: str,
        endpoint: str,
        current_request_rate: float,
        user_reputation: float,
        endpoint_sensitivity: int,
        recent_errors: int,
        time_of_day: int,
        is_authenticated: bool,
        burst_detected: bool
    ) -> Dict:
        """
        Check rate limit with RL agent.
        
        Returns:
            Decision dict with action, rate_multiplier, and reasoning
        """
        # Get decision from RL agent
        decision = self.rate_limit_agent.decide_rate_limit(
            current_request_rate=current_request_rate,
            user_reputation=user_reputation,
            endpoint_sensitivity=endpoint_sensitivity,
            recent_errors=recent_errors,
            time_of_day=time_of_day,
            is_authenticated=is_authenticated,
            burst_detected=burst_detected,
            training=False  # Production mode
        )
        
        # Publish event
        await self.event_producer.publish_rate_limit(
            tenant_id=tenant_id,
            endpoint=endpoint,
            request_rate=current_request_rate,
            action=decision["action"],
            rate_multiplier=decision["rate_multiplier"],
            reasoning=decision["reasoning"],
            user_id=user_id,
            metadata={
                "confidence": decision["confidence"],
                "q_values": decision["q_values"]
            }
        )
        
        return decision
    
    async def report_threat(
        self,
        tenant_id: str,
        threat_type: str,
        severity: str,
        source_ip: str,
        target: str,
        action_taken: str,
        details: Dict,
        user_id: Optional[str] = None
    ):
        """Report detected threat"""
        await self.event_producer.publish_threat_detection(
            tenant_id=tenant_id,
            threat_type=threat_type,
            severity=severity,
            source_ip=source_ip,
            target=target,
            action_taken=action_taken,
            details=details,
            user_id=user_id
        )
    
    async def create_incident(
        self,
        tenant_id: str,
        incident_id: str,
        incident_type: str,
        severity: str,
        description: str,
        affected_resources: list[str],
        user_id: Optional[str] = None
    ):
        """Create security incident"""
        await self.event_producer.publish_security_incident(
            tenant_id=tenant_id,
            incident_id=incident_id,
            incident_type=incident_type,
            severity=severity,
            status="open",
            description=description,
            affected_resources=affected_resources,
            user_id=user_id
        )
    
    def get_metrics(self) -> Dict:
        """Get metrics from all models"""
        return {
            "fraud_detection": self.fraud_model.get_metrics(),
            "access_control": self.access_control_agent.get_metrics(),
            "rate_limiting": self.rate_limit_agent.get_metrics()
        }
    
    async def close(self):
        """Close service connections"""
        await self.event_producer.close()
