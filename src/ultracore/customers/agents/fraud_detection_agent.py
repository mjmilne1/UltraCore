"""
UltraCore Customer Management - Fraud Detection Agent

Real-time fraud detection using:
- Anomaly detection (transaction patterns)
- Graph analysis (fraud rings)
- Behavioral analytics (device, location, time)
- ML models (supervised & unsupervised)
- Rule-based engines
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
import uuid

from ultracore.customers.agents.agent_base import (
    BaseAgent, AgentType, AgentTool, ToolType, AgentDecision
)
from ultracore.customers.core.customer_graph import get_customer_graph


# ============================================================================
# Fraud Models
# ============================================================================

class FraudType(str, Enum):
    """Types of fraud"""
    IDENTITY_THEFT = "IDENTITY_THEFT"
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    SYNTHETIC_IDENTITY = "SYNTHETIC_IDENTITY"
    MONEY_LAUNDERING = "MONEY_LAUNDERING"
    TRANSACTION_FRAUD = "TRANSACTION_FRAUD"
    APPLICATION_FRAUD = "APPLICATION_FRAUD"
    BUST_OUT = "BUST_OUT"
    FIRST_PARTY = "FIRST_PARTY"


@dataclass
class FraudSignal:
    """Fraud signal detected"""
    signal_id: str
    signal_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    confidence: Decimal
    detected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FraudAlert:
    """Fraud alert"""
    alert_id: str
    customer_id: str
    fraud_type: FraudType
    fraud_score: Decimal  # 0-100
    signals: List[FraudSignal] = field(default_factory=list)
    recommended_action: str = "MONITOR"  # MONITOR, BLOCK, ESCALATE
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Fraud Detection Agent
# ============================================================================

class FraudDetectionAgent(BaseAgent):
    """
    Real-time fraud detection agent
    
    Detection methods:
    - Rule-based (velocity checks, geolocation)
    - ML-based (anomaly detection, classification)
    - Graph-based (fraud rings, networks)
    - Behavioral (device fingerprint, patterns)
    """
    
    def __init__(self):
        system_prompt = """You are an expert fraud detection agent.
Your role is to detect and prevent fraud in real-time.

You must:
- Monitor all activities for suspicious patterns
- Detect anomalies in behavior
- Identify fraud rings through network analysis
- Score transactions for fraud risk
- Take immediate action on high-risk activities
- Minimize false positives
- Provide clear explanations for alerts

You balance fraud prevention with customer experience."""

        super().__init__(
            agent_id=f"AGENT-FRD-{uuid.uuid4().hex[:8].upper()}",
            agent_type=AgentType.FRAUD_DETECTION,
            agent_name="Fraud Detection Agent",
            system_prompt=system_prompt
        )
        
        # Fraud detection storage
        self.fraud_alerts: Dict[str, FraudAlert] = {}
        self.fraud_rules: List[Dict[str, Any]] = []
        
        # Graph for network analysis
        self.graph = get_customer_graph()
        
        # Load fraud rules
        self._load_fraud_rules()
    
    def _register_tools(self):
        """Register fraud detection tools"""
        
        self.register_tool(AgentTool(
            tool_id="anomaly_detection",
            tool_name="detect_anomalies",
            tool_type=ToolType.ML_MODEL,
            description="Detect anomalies using ML model",
            parameters={
                'type': 'object',
                'properties': {
                    'customer_id': {'type': 'string'},
                    'activity_data': {'type': 'object'}
                },
                'required': ['customer_id', 'activity_data']
            },
            function=self._detect_anomalies
        ))
        
        self.register_tool(AgentTool(
            tool_id="network_analysis",
            tool_name="analyze_fraud_network",
            tool_type=ToolType.GRAPH_QUERY,
            description="Analyze customer network for fraud rings",
            parameters={
                'type': 'object',
                'properties': {
                    'customer_id': {'type': 'string'}
                },
                'required': ['customer_id']
            },
            function=self._analyze_network
        ))
        
        self.register_tool(AgentTool(
            tool_id="rule_engine",
            tool_name="apply_fraud_rules",
            tool_type=ToolType.CALCULATION,
            description="Apply rule-based fraud detection",
            parameters={
                'type': 'object',
                'properties': {
                    'customer_id': {'type': 'string'},
                    'transaction': {'type': 'object'}
                },
                'required': ['customer_id', 'transaction']
            },
            function=self._apply_rules
        ))
    
    def _load_fraud_rules(self):
        """Load fraud detection rules"""
        
        self.fraud_rules = [
            {
                'rule_id': 'RULE-001',
                'name': 'Velocity Check - Daily',
                'description': 'Too many transactions in 24 hours',
                'threshold': 20,
                'severity': 'MEDIUM'
            },
            {
                'rule_id': 'RULE-002',
                'name': 'Large Transaction',
                'description': 'Single transaction over 10000 dollars',
                'threshold': 10000,
                'severity': 'HIGH'
            },
            {
                'rule_id': 'RULE-003',
                'name': 'Rapid Card Usage',
                'description': 'Multiple locations in short time',
                'threshold': 3,
                'severity': 'HIGH'
            },
            {
                'rule_id': 'RULE-004',
                'name': 'New Account Activity',
                'description': 'High activity on new account',
                'threshold': 5000,
                'severity': 'MEDIUM'
            }
        ]
    
    async def _make_decision(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> AgentDecision:
        """Make fraud detection decision"""
        
        decision_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"
        customer_id = context.get('customer_id')
        
        reasoning_steps = []
        evidence = {}
        signals: List[FraudSignal] = []
        
        # Run anomaly detection
        activity_data = context.get('activity_data', {})
        anomalies = await self._detect_anomalies(
            customer_id=customer_id,
            activity_data=activity_data
        )
        
        if anomalies['is_anomaly']:
            signal = FraudSignal(
                signal_id=f"SIG-{uuid.uuid4().hex[:8].upper()}",
                signal_type="ANOMALY",
                severity="HIGH",
                description=f"Anomaly detected: {anomalies['reason']}",
                confidence=Decimal(str(anomalies['confidence']))
            )
            signals.append(signal)
            reasoning_steps.append(f"⚠️ Anomaly detected: {anomalies['reason']}")
        
        # Run network analysis
        network_analysis = await self._analyze_network(customer_id=customer_id)
        
        if network_analysis['fraud_ring_detected']:
            signal = FraudSignal(
                signal_id=f"SIG-{uuid.uuid4().hex[:8].upper()}",
                signal_type="FRAUD_RING",
                severity="CRITICAL",
                description="Customer part of suspected fraud ring",
                confidence=Decimal('0.85')
            )
            signals.append(signal)
            reasoning_steps.append("🚨 Fraud ring detected in network")
        
        # Apply rules
        transaction = context.get('transaction', {})
        if transaction:
            rule_violations = await self._apply_rules(
                customer_id=customer_id,
                transaction=transaction
            )
            
            for violation in rule_violations:
                signal = FraudSignal(
                    signal_id=f"SIG-{uuid.uuid4().hex[:8].upper()}",
                    signal_type="RULE_VIOLATION",
                    severity=violation['severity'],
                    description=violation['description'],
                    confidence=Decimal('1.0')
                )
                signals.append(signal)
                reasoning_steps.append(f"⚠️ Rule violation: {violation['name']}")
        
        # Calculate fraud score
        if signals:
            fraud_score = self._calculate_fraud_score(signals)
            
            if fraud_score >= 80:
                decision_type = "BLOCK"
                recommended_action = "BLOCK"
                reasoning_steps.append(f"🚫 BLOCK - High fraud score: {fraud_score}")
            elif fraud_score >= 60:
                decision_type = "ESCALATE"
                recommended_action = "ESCALATE"
                reasoning_steps.append(f"⚠️ ESCALATE - Medium fraud score: {fraud_score}")
            else:
                decision_type = "MONITOR"
                recommended_action = "MONITOR"
                reasoning_steps.append(f"👁️ MONITOR - Low fraud score: {fraud_score}")
            
            # Create alert
            alert = FraudAlert(
                alert_id=f"ALERT-{uuid.uuid4().hex[:12].upper()}",
                customer_id=customer_id,
                fraud_type=FraudType.TRANSACTION_FRAUD,
                fraud_score=fraud_score,
                signals=signals,
                recommended_action=recommended_action,
                reason=", ".join(s.description for s in signals)
            )
            
            self.fraud_alerts[alert.alert_id] = alert
            
            evidence['fraud_alert'] = {
                'alert_id': alert.alert_id,
                'fraud_score': float(fraud_score),
                'signal_count': len(signals),
                'recommended_action': recommended_action
            }
        else:
            decision_type = "APPROVE"
            fraud_score = Decimal('0.0')
            reasoning_steps.append("✓ No fraud signals detected")
        
        decision = AgentDecision(
            decision_id=decision_id,
            agent_id=self.agent_id,
            decision_type=decision_type,
            decision=f"Fraud score: {fraud_score}",
            confidence=0.9,
            reasoning=reasoning_steps,
            evidence=evidence
        )
        
        return decision
    
    async def _detect_anomalies(
        self,
        customer_id: str,
        activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect anomalies using ML (Isolation Forest, etc.)"""
        
        # Simulated anomaly detection
        # In production: Use scikit-learn Isolation Forest, AutoEncoder, etc.
        
        is_anomaly = False
        confidence = 0.0
        reason = ""
        
        # Check for unusual patterns
        transaction_amount = activity_data.get('amount', 0)
        transaction_count = activity_data.get('count_24h', 0)
        
        if transaction_amount > 5000:
            is_anomaly = True
            confidence = 0.85
            reason = "Unusually large transaction amount"
        
        elif transaction_count > 15:
            is_anomaly = True
            confidence = 0.75
            reason = "High transaction velocity"
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'reason': reason,
            'anomaly_score': confidence * 100
        }
    
    async def _analyze_network(
        self,
        customer_id: str
    ) -> Dict[str, Any]:
        """Analyze customer network for fraud rings"""
        
        # Use graph to detect fraud rings
        fraud_rings = self.graph.find_fraud_rings(min_ring_size=3)
        
        # Check if customer is in any fraud ring
        fraud_ring_detected = False
        ring_members = []
        
        for ring in fraud_rings:
            if customer_id in ring:
                fraud_ring_detected = True
                ring_members = list(ring)
                break
        
        return {
            'fraud_ring_detected': fraud_ring_detected,
            'ring_size': len(ring_members) if fraud_ring_detected else 0,
            'ring_members': ring_members
        }
    
    async def _apply_rules(
        self,
        customer_id: str,
        transaction: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply rule-based fraud detection"""
        
        violations = []
        
        amount = Decimal(str(transaction.get('amount', 0)))
        
        # Check each rule
        for rule in self.fraud_rules:
            if rule['rule_id'] == 'RULE-002':  # Large transaction
                if amount > rule['threshold']:
                    violations.append({
                        'rule_id': rule['rule_id'],
                        'name': rule['name'],
                        'description': rule['description'],
                        'severity': rule['severity'],
                        'value': float(amount),
                        'threshold': rule['threshold']
                    })
        
        return violations
    
    def _calculate_fraud_score(
        self,
        signals: List[FraudSignal]
    ) -> Decimal:
        """Calculate overall fraud score from signals"""
        
        if not signals:
            return Decimal('0.0')
        
        # Weight by severity
        severity_weights = {
            'LOW': Decimal('10.0'),
            'MEDIUM': Decimal('30.0'),
            'HIGH': Decimal('50.0'),
            'CRITICAL': Decimal('80.0')
        }
        
        total_score = Decimal('0.0')
        for signal in signals:
            base_score = severity_weights.get(signal.severity, Decimal('10.0'))
            weighted_score = base_score * signal.confidence
            total_score += weighted_score
        
        # Cap at 100
        return min(total_score, Decimal('100.0'))


# ============================================================================
# Global Singleton
# ============================================================================

_fraud_detection_agent: Optional[FraudDetectionAgent] = None

def get_fraud_detection_agent() -> FraudDetectionAgent:
    """Get singleton fraud detection agent"""
    global _fraud_detection_agent
    if _fraud_detection_agent is None:
        _fraud_detection_agent = FraudDetectionAgent()
    return _fraud_detection_agent
