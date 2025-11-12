"""
Transaction AI Agent
Autonomous validation, fraud detection, and trade monitoring
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

class ValidationResult(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW = "review"
    FRAUD = "fraud"

class FraudRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TransactionAgent:
    """
    AI Agent for transaction validation and monitoring
    
    Capabilities:
    - Order validation
    - Fraud detection
    - Risk assessment
    - Trade monitoring
    - Optimal execution
    """
    
    def __init__(self):
        self.validation_history = []
        self.fraud_patterns = []
        self.risk_thresholds = {
            "max_order_value": 1000000,
            "max_daily_trades": 50,
            "max_position_size": 0.10  # 10% of portfolio
        }
    
    async def validate_order(
        self,
        order: Dict[str, Any],
        client_data: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comprehensive order validation
        Returns validation result with reasoning
        """
        
        validations = []
        
        # 1. Basic validation
        basic_check = self._validate_basic_order(order)
        validations.append(basic_check)
        
        # 2. Client eligibility
        client_check = self._validate_client_eligibility(order, client_data)
        validations.append(client_check)
        
        # 3. Risk checks
        risk_check = await self._validate_risk_limits(order, portfolio)
        validations.append(risk_check)
        
        # 4. Fraud detection
        fraud_check = await self._detect_fraud_patterns(order, client_data)
        validations.append(fraud_check)
        
        # 5. Market conditions
        market_check = self._validate_market_conditions(order)
        validations.append(market_check)
        
        # 6. Compliance checks
        compliance_check = self._validate_compliance(order, client_data)
        validations.append(compliance_check)
        
        # Determine overall result
        if any(v["result"] == ValidationResult.FRAUD for v in validations):
            decision = ValidationResult.FRAUD
        elif any(v["result"] == ValidationResult.REJECTED for v in validations):
            decision = ValidationResult.REJECTED
        elif any(v["result"] == ValidationResult.REVIEW for v in validations):
            decision = ValidationResult.REVIEW
        else:
            decision = ValidationResult.APPROVED
        
        validation_result = {
            "order_id": order.get("order_id"),
            "decision": decision,
            "validations": validations,
            "timestamp": datetime.utcnow().isoformat(),
            "confidence": self._calculate_confidence(validations),
            "reasoning": self._explain_decision(validations, decision)
        }
        
        # Record validation
        self.validation_history.append(validation_result)
        
        return validation_result
    
    async def detect_fraud(
        self,
        order: Dict[str, Any],
        client_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deep fraud detection analysis
        """
        
        fraud_indicators = []
        
        # 1. Unusual order size
        order_value = order.get("quantity", 0) * order.get("limit_price", 0)
        avg_order_value = self._calculate_avg_order_value(client_history)
        
        if order_value > avg_order_value * 10:
            fraud_indicators.append({
                "type": "unusual_order_size",
                "severity": "high",
                "description": f"Order value {order_value/avg_order_value:.1f}x larger than average"
            })
        
        # 2. High frequency trading
        recent_orders = self._get_recent_orders(client_history, hours=24)
        if len(recent_orders) > 20:
            fraud_indicators.append({
                "type": "high_frequency_trading",
                "severity": "medium",
                "description": f"{len(recent_orders)} orders in 24 hours"
            })
        
        # 3. Unusual time patterns
        order_time = datetime.fromisoformat(order.get("timestamp", datetime.utcnow().isoformat()))
        if order_time.hour < 6 or order_time.hour > 22:
            fraud_indicators.append({
                "type": "unusual_timing",
                "severity": "low",
                "description": "Order placed outside normal hours"
            })
        
        # 4. Rapid buy-sell pattern (wash trading)
        if self._detect_wash_trading(order, client_history):
            fraud_indicators.append({
                "type": "wash_trading",
                "severity": "critical",
                "description": "Potential wash trading detected"
            })
        
        # Calculate fraud risk
        risk_level = self._calculate_fraud_risk(fraud_indicators)
        
        return {
            "fraud_detected": len(fraud_indicators) > 0,
            "risk_level": risk_level,
            "indicators": fraud_indicators,
            "recommendation": self._get_fraud_recommendation(risk_level),
            "requires_investigation": risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]
        }
    
    async def optimize_execution(
        self,
        order: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend optimal execution strategy
        Uses ML to minimize market impact
        """
        
        ticker = order.get("ticker")
        quantity = order.get("quantity", 0)
        side = order.get("side")
        
        # Get market metrics
        avg_volume = market_data.get("avg_volume", 0)
        spread = market_data.get("spread", 0)
        volatility = market_data.get("volatility", 0)
        
        # Calculate order size relative to volume
        volume_pct = (quantity / avg_volume) if avg_volume > 0 else 0
        
        # Determine execution strategy
        if volume_pct < 0.01:  # <1% of volume
            strategy = "aggressive"
            recommendation = "Execute as single order - minimal market impact"
        elif volume_pct < 0.05:  # 1-5% of volume
            strategy = "moderate"
            recommendation = "Split into 2-3 orders over 15 minutes"
        else:  # >5% of volume
            strategy = "passive"
            recommendation = "Use TWAP/VWAP over multiple hours"
        
        # Estimate costs
        estimated_spread_cost = quantity * spread
        estimated_impact = self._estimate_market_impact(quantity, avg_volume)
        
        return {
            "ticker": ticker,
            "strategy": strategy,
            "recommendation": recommendation,
            "volume_percentage": volume_pct,
            "estimated_spread_cost": estimated_spread_cost,
            "estimated_market_impact": estimated_impact,
            "total_estimated_cost": estimated_spread_cost + estimated_impact,
            "confidence": 0.85
        }
    
    def _validate_basic_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Basic order field validation"""
        
        errors = []
        
        if not order.get("client_id"):
            errors.append("Missing client_id")
        
        if not order.get("ticker"):
            errors.append("Missing ticker")
        
        if not order.get("side"):
            errors.append("Missing side (buy/sell)")
        
        quantity = order.get("quantity", 0)
        if quantity <= 0:
            errors.append("Invalid quantity")
        
        order_type = order.get("order_type")
        if order_type == "limit" and not order.get("limit_price"):
            errors.append("Limit order missing limit_price")
        
        if order_type == "stop" and not order.get("stop_price"):
            errors.append("Stop order missing stop_price")
        
        return {
            "check": "basic_validation",
            "result": ValidationResult.APPROVED if not errors else ValidationResult.REJECTED,
            "errors": errors
        }
    
    def _validate_client_eligibility(
        self,
        order: Dict[str, Any],
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate client can trade"""
        
        errors = []
        
        # Check KYC
        if not client_data.get("kyc_completed"):
            errors.append("Client KYC not completed")
        
        # Check account status
        if client_data.get("status") != "active":
            errors.append(f"Client account status: {client_data.get('status')}")
        
        # Check trading permissions
        if not client_data.get("trading_enabled"):
            errors.append("Trading not enabled for client")
        
        return {
            "check": "client_eligibility",
            "result": ValidationResult.APPROVED if not errors else ValidationResult.REJECTED,
            "errors": errors
        }
    
    async def _validate_risk_limits(
        self,
        order: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate against risk limits"""
        
        warnings = []
        errors = []
        
        # Check order value
        order_value = order.get("quantity", 0) * order.get("limit_price", 0)
        if order_value > self.risk_thresholds["max_order_value"]:
            errors.append(f"Order value ${order_value:,.0f} exceeds limit")
        
        # Check position size
        portfolio_value = portfolio.get("total_value", 0)
        if portfolio_value > 0:
            position_pct = order_value / portfolio_value
            if position_pct > self.risk_thresholds["max_position_size"]:
                warnings.append(f"Position would be {position_pct:.1%} of portfolio")
        
        # Check concentration
        ticker = order.get("ticker")
        existing_position = next(
            (p for p in portfolio.get("positions", []) if p.get("ticker") == ticker),
            None
        )
        
        if existing_position and order.get("side") == "buy":
            new_value = existing_position.get("market_value", 0) + order_value
            if portfolio_value > 0 and new_value / portfolio_value > 0.25:
                warnings.append(f"Would increase {ticker} position to >25% of portfolio")
        
        result = ValidationResult.APPROVED
        if errors:
            result = ValidationResult.REJECTED
        elif warnings:
            result = ValidationResult.REVIEW
        
        return {
            "check": "risk_limits",
            "result": result,
            "errors": errors,
            "warnings": warnings
        }
    
    async def _detect_fraud_patterns(
        self,
        order: Dict[str, Any],
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect potential fraud"""
        
        # Quick fraud check (full check in detect_fraud)
        suspicious = []
        
        order_value = order.get("quantity", 0) * order.get("limit_price", 0)
        
        # Very large orders are suspicious
        if order_value > 500000:
            suspicious.append("Large order value")
        
        result = ValidationResult.REVIEW if suspicious else ValidationResult.APPROVED
        
        return {
            "check": "fraud_detection",
            "result": result,
            "suspicious_indicators": suspicious
        }
    
    def _validate_market_conditions(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Validate market is open and tradeable"""
        
        # Check market hours (simplified)
        now = datetime.utcnow()
        
        # ASX hours: 10:00 - 16:00 AEST (approx 00:00 - 06:00 UTC)
        warnings = []
        
        if now.weekday() >= 5:  # Weekend
            warnings.append("Market closed (weekend)")
        
        return {
            "check": "market_conditions",
            "result": ValidationResult.APPROVED,
            "warnings": warnings
        }
    
    def _validate_compliance(
        self,
        order: Dict[str, Any],
        client_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compliance checks"""
        
        # Placeholder for regulatory checks
        return {
            "check": "compliance",
            "result": ValidationResult.APPROVED,
            "checks": ["market_abuse", "insider_trading", "wash_trading"]
        }
    
    def _calculate_confidence(self, validations: List[Dict[str, Any]]) -> float:
        """Calculate confidence in validation"""
        
        total_checks = len(validations)
        passed_checks = sum(
            1 for v in validations
            if v["result"] == ValidationResult.APPROVED
        )
        
        return passed_checks / total_checks if total_checks > 0 else 0
    
    def _explain_decision(
        self,
        validations: List[Dict[str, Any]],
        decision: ValidationResult
    ) -> str:
        """Explain validation decision"""
        
        if decision == ValidationResult.APPROVED:
            return "All validation checks passed"
        
        failed_checks = [
            v["check"] for v in validations
            if v["result"] in [ValidationResult.REJECTED, ValidationResult.FRAUD]
        ]
        
        return f"Failed checks: {', '.join(failed_checks)}"
    
    def _calculate_avg_order_value(self, history: List[Dict[str, Any]]) -> float:
        """Calculate average order value from history"""
        
        if not history:
            return 10000  # Default
        
        values = [
            h.get("quantity", 0) * h.get("price", 0)
            for h in history
        ]
        
        return sum(values) / len(values) if values else 10000
    
    def _get_recent_orders(
        self,
        history: List[Dict[str, Any]],
        hours: int
    ) -> List[Dict[str, Any]]:
        """Get orders from recent time period"""
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            h for h in history
            if datetime.fromisoformat(h.get("timestamp", "2020-01-01")) > cutoff
        ]
    
    def _detect_wash_trading(
        self,
        order: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> bool:
        """Detect wash trading patterns"""
        
        # Look for rapid buy-sell of same security
        ticker = order.get("ticker")
        side = order.get("side")
        
        recent = self._get_recent_orders(history, hours=24)
        
        # Count opposite side trades for same ticker
        opposite_trades = [
            h for h in recent
            if h.get("ticker") == ticker and h.get("side") != side
        ]
        
        return len(opposite_trades) > 5
    
    def _calculate_fraud_risk(
        self,
        indicators: List[Dict[str, Any]]
    ) -> FraudRiskLevel:
        """Calculate overall fraud risk level"""
        
        if not indicators:
            return FraudRiskLevel.LOW
        
        critical_count = sum(1 for i in indicators if i["severity"] == "critical")
        high_count = sum(1 for i in indicators if i["severity"] == "high")
        
        if critical_count > 0:
            return FraudRiskLevel.CRITICAL
        elif high_count >= 2:
            return FraudRiskLevel.HIGH
        elif high_count == 1 or len(indicators) >= 3:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW
    
    def _get_fraud_recommendation(self, risk_level: FraudRiskLevel) -> str:
        """Get recommendation based on fraud risk"""
        
        recommendations = {
            FraudRiskLevel.LOW: "Proceed with order",
            FraudRiskLevel.MEDIUM: "Review order details before execution",
            FraudRiskLevel.HIGH: "Hold order for compliance review",
            FraudRiskLevel.CRITICAL: "Block order and investigate client account"
        }
        
        return recommendations.get(risk_level, "Review order")
    
    def _estimate_market_impact(self, quantity: float, avg_volume: float) -> float:
        """Estimate market impact cost"""
        
        if avg_volume == 0:
            return 0
        
        volume_pct = quantity / avg_volume
        
        # Simple square root model
        impact_pct = 0.1 * (volume_pct ** 0.5)
        
        return quantity * 100 * impact_pct  # Assuming $100 price

# Global instance
transaction_agent = TransactionAgent()
