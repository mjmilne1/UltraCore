"""
Transaction Monitoring Service.

Real-time monitoring of transactions for suspicious activity patterns.
Implements rule-based detection for AML/CTF compliance.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from ..models import (
    AlertPriority,
    MonitoringRuleType,
    RiskLevel,
    SuspiciousActivity,
    TransactionMonitoring,
)


class MonitoringRule:
    """Base class for monitoring rules."""
    
    def __init__(
        self,
        rule_type: MonitoringRuleType,
        name: str,
        severity: str,
        enabled: bool = True
    ):
        self.rule_type = rule_type
        self.name = name
        self.severity = severity
        self.enabled = enabled
    
    def evaluate(self, transaction: Dict, context: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Evaluate rule against transaction.
        
        Returns:
            (triggered, details) tuple
        """
        raise NotImplementedError


class ThresholdRule(MonitoringRule):
    """Threshold-based monitoring rule."""
    
    def __init__(
        self,
        name: str,
        threshold: Decimal,
        severity: str = "medium",
        enabled: bool = True
    ):
        super().__init__(MonitoringRuleType.THRESHOLD, name, severity, enabled)
        self.threshold = threshold
    
    def evaluate(self, transaction: Dict, context: Dict) -> Tuple[bool, Optional[Dict]]:
        """Check if transaction exceeds threshold."""
        amount = Decimal(str(transaction.get("amount", 0)))
        
        if amount >= self.threshold:
            return True, {
                "amount": float(amount),
                "threshold": float(self.threshold),
                "excess": float(amount - self.threshold)
            }
        
        return False, None


class VelocityRule(MonitoringRule):
    """Velocity-based monitoring rule (frequency/volume over time)."""
    
    def __init__(
        self,
        name: str,
        max_transactions: int,
        time_window_hours: int,
        severity: str = "medium",
        enabled: bool = True
    ):
        super().__init__(MonitoringRuleType.VELOCITY, name, severity, enabled)
        self.max_transactions = max_transactions
        self.time_window_hours = time_window_hours
    
    def evaluate(self, transaction: Dict, context: Dict) -> Tuple[bool, Optional[Dict]]:
        """Check transaction velocity."""
        recent_transactions = context.get("recent_transactions", [])
        
        # Count transactions in time window
        cutoff_time = datetime.utcnow() - timedelta(hours=self.time_window_hours)
        recent_count = sum(
            1 for tx in recent_transactions
            if datetime.fromisoformat(tx.get("timestamp", "")) > cutoff_time
        )
        
        if recent_count >= self.max_transactions:
            return True, {
                "transaction_count": recent_count,
                "max_allowed": self.max_transactions,
                "time_window_hours": self.time_window_hours
            }
        
        return False, None


class PatternRule(MonitoringRule):
    """Pattern-based monitoring rule (structuring, round amounts, etc.)."""
    
    def __init__(
        self,
        name: str,
        pattern_type: str,
        severity: str = "high",
        enabled: bool = True
    ):
        super().__init__(MonitoringRuleType.PATTERN, name, severity, enabled)
        self.pattern_type = pattern_type
    
    def evaluate(self, transaction: Dict, context: Dict) -> Tuple[bool, Optional[Dict]]:
        """Check for suspicious patterns."""
        if self.pattern_type == "structuring":
            return self._check_structuring(transaction, context)
        elif self.pattern_type == "round_amounts":
            return self._check_round_amounts(transaction, context)
        elif self.pattern_type == "rapid_movement":
            return self._check_rapid_movement(transaction, context)
        
        return False, None
    
    def _check_structuring(
        self,
        transaction: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[Dict]]:
        """Check for structuring (breaking large amounts into smaller ones)."""
        amount = Decimal(str(transaction.get("amount", 0)))
        recent_transactions = context.get("recent_transactions", [])
        
        # Check for multiple transactions just below reporting threshold
        threshold = Decimal("10000")  # AUD 10,000 threshold
        margin = Decimal("1000")  # Within $1,000 of threshold
        
        # Count recent transactions close to threshold
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        similar_transactions = [
            tx for tx in recent_transactions
            if (
                datetime.fromisoformat(tx.get("timestamp", "")) > cutoff_time
                and threshold - margin <= Decimal(str(tx.get("amount", 0))) < threshold
            )
        ]
        
        if len(similar_transactions) >= 3:  # 3+ transactions in pattern
            return True, {
                "pattern": "structuring",
                "transaction_count": len(similar_transactions),
                "threshold": float(threshold),
                "description": "Multiple transactions just below reporting threshold"
            }
        
        return False, None
    
    def _check_round_amounts(
        self,
        transaction: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[Dict]]:
        """Check for suspicious round amounts."""
        amount = Decimal(str(transaction.get("amount", 0)))
        
        # Check if amount is suspiciously round (e.g., $10,000, $50,000)
        if amount >= Decimal("5000"):
            # Check if divisible by 1000 or 5000
            if amount % Decimal("5000") == 0 or amount % Decimal("1000") == 0:
                return True, {
                    "pattern": "round_amounts",
                    "amount": float(amount),
                    "description": "Large round amount transaction"
                }
        
        return False, None
    
    def _check_rapid_movement(
        self,
        transaction: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[Dict]]:
        """Check for rapid movement of funds (layering)."""
        recent_transactions = context.get("recent_transactions", [])
        
        # Check for rapid in-out pattern
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent_hour = [
            tx for tx in recent_transactions
            if datetime.fromisoformat(tx.get("timestamp", "")) > cutoff_time
        ]
        
        if len(recent_hour) >= 5:  # 5+ transactions in 1 hour
            return True, {
                "pattern": "rapid_movement",
                "transaction_count": len(recent_hour),
                "time_window": "1 hour",
                "description": "Rapid movement of funds detected"
            }
        
        return False, None


class GeographicRule(MonitoringRule):
    """Geographic risk monitoring rule."""
    
    def __init__(
        self,
        name: str,
        high_risk_countries: List[str],
        severity: str = "high",
        enabled: bool = True
    ):
        super().__init__(MonitoringRuleType.GEOGRAPHIC, name, severity, enabled)
        self.high_risk_countries = high_risk_countries
    
    def evaluate(self, transaction: Dict, context: Dict) -> Tuple[bool, Optional[Dict]]:
        """Check for high-risk geographic locations."""
        destination_country = transaction.get("destination_country", "")
        origin_country = transaction.get("origin_country", "")
        
        high_risk = []
        if destination_country in self.high_risk_countries:
            high_risk.append(f"destination: {destination_country}")
        if origin_country in self.high_risk_countries:
            high_risk.append(f"origin: {origin_country}")
        
        if high_risk:
            return True, {
                "high_risk_locations": high_risk,
                "description": "Transaction involving high-risk jurisdiction"
            }
        
        return False, None


class TransactionMonitoringService:
    """
    Transaction Monitoring Service.
    
    Real-time monitoring of transactions for suspicious activity.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.rules: List[MonitoringRule] = []
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize monitoring rules."""
        # Threshold rules (AUSTRAC reporting thresholds)
        self.rules.append(
            ThresholdRule(
                name="Large Cash Transaction",
                threshold=Decimal("10000"),  # AUD 10,000
                severity="high"
            )
        )
        
        self.rules.append(
            ThresholdRule(
                name="Very Large Transaction",
                threshold=Decimal("100000"),  # AUD 100,000
                severity="critical"
            )
        )
        
        # Velocity rules
        self.rules.append(
            VelocityRule(
                name="High Transaction Frequency",
                max_transactions=10,
                time_window_hours=24,
                severity="medium"
            )
        )
        
        self.rules.append(
            VelocityRule(
                name="Rapid Transaction Burst",
                max_transactions=5,
                time_window_hours=1,
                severity="high"
            )
        )
        
        # Pattern rules
        self.rules.append(
            PatternRule(
                name="Structuring Detection",
                pattern_type="structuring",
                severity="critical"
            )
        )
        
        self.rules.append(
            PatternRule(
                name="Round Amount Detection",
                pattern_type="round_amounts",
                severity="medium"
            )
        )
        
        self.rules.append(
            PatternRule(
                name="Rapid Fund Movement",
                pattern_type="rapid_movement",
                severity="high"
            )
        )
        
        # Geographic rules
        # High-risk countries per FATF guidance
        high_risk_countries = [
            "KP",  # North Korea
            "IR",  # Iran
            "MM",  # Myanmar
            "SY",  # Syria
            # Add more as needed
        ]
        
        self.rules.append(
            GeographicRule(
                name="High Risk Jurisdiction",
                high_risk_countries=high_risk_countries,
                severity="critical"
            )
        )
    
    def monitor_transaction(
        self,
        transaction: Dict,
        context: Optional[Dict] = None
    ) -> TransactionMonitoring:
        """
        Monitor a transaction for suspicious activity.
        
        Args:
            transaction: Transaction details
            context: Additional context (customer history, etc.)
        
        Returns:
            TransactionMonitoring result
        """
        if context is None:
            context = {}
        
        # Create monitoring record
        monitoring = TransactionMonitoring(
            tenant_id=self.tenant_id,
            transaction_id=transaction.get("transaction_id", ""),
            customer_id=transaction.get("customer_id", ""),
            account_id=transaction.get("account_id", ""),
            amount=Decimal(str(transaction.get("amount", 0))),
            currency=transaction.get("currency", "AUD"),
            transaction_type=transaction.get("transaction_type", "")
        )
        
        # Evaluate all rules
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            triggered, details = rule.evaluate(transaction, context)
            
            if triggered:
                monitoring.add_rule_trigger(
                    rule_type=rule.rule_type,
                    rule_name=rule.name,
                    severity=rule.severity,
                    details=details or {}
                )
        
        # Calculate overall risk score
        monitoring.calculate_risk_score()
        
        return monitoring
    
    def should_generate_alert(self, monitoring: TransactionMonitoring) -> bool:
        """Determine if an alert should be generated."""
        # Generate alert for high or critical risk
        return monitoring.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def create_suspicious_activity_alert(
        self,
        monitoring: TransactionMonitoring,
        customer_data: Dict
    ) -> SuspiciousActivity:
        """Create suspicious activity alert from monitoring result."""
        # Determine alert priority
        priority_map = {
            RiskLevel.LOW: AlertPriority.LOW,
            RiskLevel.MEDIUM: AlertPriority.MEDIUM,
            RiskLevel.HIGH: AlertPriority.HIGH,
            RiskLevel.CRITICAL: AlertPriority.CRITICAL
        }
        
        priority = priority_map.get(monitoring.risk_level, AlertPriority.MEDIUM)
        
        # Generate alert title and description
        rule_names = [rule["rule_name"] for rule in monitoring.rules_triggered]
        title = f"Suspicious Activity Detected: {', '.join(rule_names[:2])}"
        
        description = (
            f"Transaction {monitoring.transaction_id} triggered {len(monitoring.rules_triggered)} "
            f"monitoring rules with risk score {monitoring.risk_score}/100."
        )
        
        # Extract indicators
        indicators = [
            f"{rule['rule_name']}: {rule['details'].get('description', 'Triggered')}"
            for rule in monitoring.rules_triggered
        ]
        
        # Create alert
        alert = SuspiciousActivity(
            tenant_id=self.tenant_id,
            customer_id=monitoring.customer_id,
            account_id=monitoring.account_id,
            transaction_ids=[monitoring.transaction_id],
            alert_type="transaction_monitoring",
            priority=priority,
            risk_level=monitoring.risk_level,
            risk_score=monitoring.risk_score,
            title=title,
            description=description,
            indicators=indicators
        )
        
        return alert
    
    def add_rule(self, rule: MonitoringRule):
        """Add custom monitoring rule."""
        self.rules.append(rule)
    
    def disable_rule(self, rule_name: str):
        """Disable a monitoring rule."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                break
    
    def enable_rule(self, rule_name: str):
        """Enable a monitoring rule."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                break
    
    def get_rules(self) -> List[Dict]:
        """Get all monitoring rules."""
        return [
            {
                "name": rule.name,
                "type": rule.rule_type.value,
                "severity": rule.severity,
                "enabled": rule.enabled
            }
            for rule in self.rules
        ]
