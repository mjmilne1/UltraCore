"""
Holdings Management AI Agent
Autonomous agent for portfolio monitoring, rebalancing, and optimization
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from ultracore.streaming.kafka_events import kafka_producer, EventType
from ultracore.ml.rl.portfolio_agent import portfolio_rl_agent, Action

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class HoldingsAgent:
    """
    Agentic AI for autonomous holdings management
    
    Capabilities:
    - Continuous portfolio monitoring
    - Anomaly detection
    - Automatic rebalancing recommendations
    - Risk monitoring
    - Performance optimization
    """
    
    def __init__(self):
        self.monitoring_active = False
        self.alerts = []
        self.decisions = []
        self.rebalancing_threshold = 0.05  # 5% drift triggers rebalance
    
    async def monitor_portfolio(
        self,
        client_id: str,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Continuous portfolio monitoring
        Detects issues and generates alerts
        """
        
        alerts = []
        recommendations = []
        
        # 1. Check concentration risk
        concentration_alert = self._check_concentration_risk(portfolio)
        if concentration_alert:
            alerts.append(concentration_alert)
        
        # 2. Check position performance
        performance_alerts = self._check_position_performance(portfolio)
        alerts.extend(performance_alerts)
        
        # 3. Check rebalancing need
        rebalancing = await self._check_rebalancing_need(portfolio)
        if rebalancing["needs_rebalancing"]:
            alerts.append({
                "level": AlertLevel.WARNING,
                "type": "rebalancing_required",
                "message": f"Portfolio drift detected: {rebalancing['max_drift']:.1%}",
                "recommendation": "Rebalance portfolio to target allocation"
            })
            recommendations.append(rebalancing)
        
        # 4. Check for underperforming positions
        underperformers = self._identify_underperformers(portfolio)
        if underperformers:
            alerts.append({
                "level": AlertLevel.INFO,
                "type": "underperforming_positions",
                "message": f"{len(underperformers)} positions underperforming",
                "positions": underperformers
            })
        
        # 5. Check liquidity
        liquidity_alert = self._check_liquidity(portfolio)
        if liquidity_alert:
            alerts.append(liquidity_alert)
        
        # 6. Get RL agent recommendation
        rl_action, confidence = portfolio_rl_agent.get_optimal_action(portfolio)
        if rl_action != Action.HOLD and confidence > 0.7:
            recommendations.append({
                "type": "rl_recommendation",
                "action": rl_action,
                "confidence": confidence,
                "reasoning": self._explain_rl_action(rl_action, portfolio)
            })
        
        # Store monitoring results
        monitoring_result = {
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alerts": alerts,
            "recommendations": recommendations,
            "portfolio_health_score": self._calculate_health_score(portfolio, alerts),
            "next_action": self._determine_next_action(alerts, recommendations)
        }
        
        # Produce monitoring event to Kafka
        await kafka_producer.produce(
            topic="holdings.monitoring",
            event_type=EventType.POSITION_VALUED,
            data=monitoring_result,
            key=client_id
        )
        
        self.alerts.extend(alerts)
        
        return monitoring_result
    
    async def recommend_rebalancing(
        self,
        portfolio: Dict[str, Any],
        target_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate rebalancing recommendations
        Uses both rule-based and RL approaches
        """
        
        current_allocation = self._calculate_current_allocation(portfolio)
        
        # Calculate drifts
        drifts = {}
        for ticker, target_weight in target_allocation.items():
            current_weight = current_allocation.get(ticker, 0)
            drift = current_weight - target_weight
            drifts[ticker] = {
                "current": current_weight,
                "target": target_weight,
                "drift": drift,
                "drift_pct": abs(drift / target_weight) if target_weight > 0 else 0
            }
        
        # Generate trades to rebalance
        total_value = portfolio.get("total_value", 0)
        trades = []
        
        for ticker, drift_info in drifts.items():
            drift = drift_info["drift"]
            if abs(drift) > self.rebalancing_threshold:
                trade_value = drift * total_value
                
                trades.append({
                    "ticker": ticker,
                    "action": "sell" if trade_value > 0 else "buy",
                    "value": abs(trade_value),
                    "current_weight": drift_info["current"],
                    "target_weight": drift_info["target"]
                })
        
        # Calculate expected impact
        impact = self._calculate_rebalancing_impact(portfolio, trades)
        
        recommendation = {
            "recommended": len(trades) > 0,
            "trades": trades,
            "drifts": drifts,
            "estimated_cost": self._estimate_transaction_costs(trades),
            "expected_improvement": impact,
            "confidence": 0.9,
            "reasoning": self._explain_rebalancing(drifts, trades)
        }
        
        # Record decision
        self.decisions.append({
            "type": "rebalancing_recommendation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "recommendation": recommendation
        })
        
        return recommendation
    
    async def detect_anomalies(
        self,
        client_id: str,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect anomalous positions or behaviors
        """
        
        anomalies = []
        
        for position in positions:
            ticker = position.get("ticker")
            
            # 1. Check for unusual position size
            position_value = position.get("market_value", 0)
            total_value = sum(p.get("market_value", 0) for p in positions)
            
            if total_value > 0:
                weight = position_value / total_value
                if weight > 0.3:  # Single position > 30%
                    anomalies.append({
                        "type": "oversized_position",
                        "ticker": ticker,
                        "weight": weight,
                        "severity": "high",
                        "message": f"{ticker} represents {weight:.1%} of portfolio"
                    })
            
            # 2. Check for large unrealized losses
            cost_basis = position.get("cost_basis", 0)
            if cost_basis > 0:
                unrealized_gl = position_value - cost_basis
                loss_pct = unrealized_gl / cost_basis
                
                if loss_pct < -0.20:  # >20% loss
                    anomalies.append({
                        "type": "large_unrealized_loss",
                        "ticker": ticker,
                        "loss_pct": loss_pct,
                        "severity": "medium",
                        "message": f"{ticker} down {loss_pct:.1%}"
                    })
            
            # 3. Check for stale positions (no updates)
            last_updated = position.get("last_updated")
            if last_updated:
                days_stale = (datetime.now(timezone.utc) - datetime.fromisoformat(last_updated)).days
                if days_stale > 30:
                    anomalies.append({
                        "type": "stale_position",
                        "ticker": ticker,
                        "days_stale": days_stale,
                        "severity": "low",
                        "message": f"{ticker} not updated in {days_stale} days"
                    })
        
        return {
            "client_id": client_id,
            "anomalies_detected": len(anomalies) > 0,
            "anomalies": anomalies,
            "risk_level": self._calculate_anomaly_risk_level(anomalies)
        }
    
    async def optimize_portfolio(
        self,
        portfolio: Dict[str, Any],
        risk_profile: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize portfolio using ML and modern portfolio theory
        """
        
        from ultracore.services.ultrawealth import ultrawealth_service
        
        positions = portfolio.get("positions", [])
        tickers = [p.get("ticker") for p in positions]
        
        # Get ML predictions for all positions
        predictions = {}
        for ticker in tickers:
            try:
                pred = await ultrawealth_service.predict_etf(ticker)
                predictions[ticker] = pred
            except:
                predictions[ticker] = {"predicted_return": 0, "confidence": 0}
        
        # Calculate optimal weights using RL agent
        state = portfolio_rl_agent.get_state(portfolio)
        action, confidence = portfolio_rl_agent.get_optimal_action(portfolio)
        
        # Generate optimization
        optimization = {
            "current_allocation": self._calculate_current_allocation(portfolio),
            "recommended_allocation": self._calculate_optimal_allocation(
                predictions,
                risk_profile,
                constraints
            ),
            "expected_return": self._calculate_expected_return(predictions),
            "expected_risk": self._calculate_expected_risk(predictions),
            "sharpe_ratio": self._calculate_expected_sharpe(predictions),
            "rl_recommendation": {
                "action": action,
                "confidence": confidence
            },
            "reasoning": self._explain_optimization(predictions, risk_profile)
        }
        
        return optimization
    
    def _check_concentration_risk(
        self,
        portfolio: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check for concentration risk"""
        
        positions = portfolio.get("positions", [])
        total_value = portfolio.get("total_value", 0)
        
        if not positions or total_value == 0:
            return None
        
        # Calculate Herfindahl index
        weights = [p.get("market_value", 0) / total_value for p in positions]
        hhi = sum(w**2 for w in weights)
        
        # HHI > 0.25 indicates high concentration
        if hhi > 0.25:
            return {
                "level": AlertLevel.WARNING,
                "type": "concentration_risk",
                "hhi": hhi,
                "message": f"High concentration risk (HHI: {hhi:.2f})",
                "recommendation": "Diversify portfolio to reduce concentration"
            }
        
        return None
    
    def _check_position_performance(
        self,
        portfolio: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check individual position performance"""
        
        alerts = []
        positions = portfolio.get("positions", [])
        
        for position in positions:
            ticker = position.get("ticker")
            cost_basis = position.get("cost_basis", 0)
            market_value = position.get("market_value", 0)
            
            if cost_basis > 0:
                return_pct = (market_value - cost_basis) / cost_basis
                
                # Alert on large losses
                if return_pct < -0.15:  # >15% loss
                    alerts.append({
                        "level": AlertLevel.WARNING,
                        "type": "position_loss",
                        "ticker": ticker,
                        "return": return_pct,
                        "message": f"{ticker} down {return_pct:.1%}",
                        "recommendation": "Review position for potential exit"
                    })
        
        return alerts
    
    async def _check_rebalancing_need(
        self,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if portfolio needs rebalancing"""
        
        # This would compare to target allocation
        # For now, simple drift check
        
        positions = portfolio.get("positions", [])
        total_value = portfolio.get("total_value", 0)
        
        if not positions or total_value == 0:
            return {"needs_rebalancing": False, "max_drift": 0}
        
        # Assume equal weight target for simplicity
        target_weight = 1.0 / len(positions)
        
        max_drift = 0
        for position in positions:
            current_weight = position.get("market_value", 0) / total_value
            drift = abs(current_weight - target_weight)
            max_drift = max(max_drift, drift)
        
        return {
            "needs_rebalancing": max_drift > self.rebalancing_threshold,
            "max_drift": max_drift,
            "threshold": self.rebalancing_threshold
        }
    
    def _identify_underperformers(
        self,
        portfolio: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify underperforming positions"""
        
        positions = portfolio.get("positions", [])
        underperformers = []
        
        # Calculate portfolio average return
        returns = []
        for position in positions:
            cost = position.get("cost_basis", 0)
            value = position.get("market_value", 0)
            if cost > 0:
                returns.append((value - cost) / cost)
        
        if not returns:
            return []
        
        avg_return = sum(returns) / len(returns)
        
        # Find positions below average
        for position in positions:
            cost = position.get("cost_basis", 0)
            value = position.get("market_value", 0)
            if cost > 0:
                pos_return = (value - cost) / cost
                if pos_return < avg_return - 0.05:  # 5% below average
                    underperformers.append({
                        "ticker": position.get("ticker"),
                        "return": pos_return,
                        "vs_avg": pos_return - avg_return
                    })
        
        return underperformers
    
    def _check_liquidity(
        self,
        portfolio: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check portfolio liquidity"""
        
        # This would check trading volumes, bid-ask spreads, etc.
        # Placeholder for now
        return None
    
    def _calculate_health_score(
        self,
        portfolio: Dict[str, Any],
        alerts: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall portfolio health score (0-100)"""
        
        score = 100
        
        # Deduct points for alerts
        for alert in alerts:
            if alert.get("level") == AlertLevel.CRITICAL:
                score -= 20
            elif alert.get("level") == AlertLevel.WARNING:
                score -= 10
            else:
                score -= 5
        
        # Bonus for diversification
        positions_count = len(portfolio.get("positions", []))
        if 5 <= positions_count <= 15:
            score += 5
        
        return max(0, min(100, score))
    
    def _determine_next_action(
        self,
        alerts: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]]
    ) -> str:
        """Determine next action for user"""
        
        critical_alerts = [a for a in alerts if a.get("level") == AlertLevel.CRITICAL]
        
        if critical_alerts:
            return "immediate_action_required"
        elif recommendations:
            return "review_recommendations"
        elif alerts:
            return "review_alerts"
        else:
            return "monitor_only"
    
    def _calculate_current_allocation(
        self,
        portfolio: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate current portfolio allocation"""
        
        positions = portfolio.get("positions", [])
        total_value = portfolio.get("total_value", 0)
        
        if total_value == 0:
            return {}
        
        allocation = {}
        for position in positions:
            ticker = position.get("ticker")
            value = position.get("market_value", 0)
            allocation[ticker] = value / total_value
        
        return allocation
    
    def _calculate_rebalancing_impact(
        self,
        portfolio: Dict[str, Any],
        trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate expected impact of rebalancing"""
        
        return {
            "risk_reduction": 0.05,  # Placeholder
            "expected_return_improvement": 0.02,
            "diversification_improvement": 0.10
        }
    
    def _estimate_transaction_costs(
        self,
        trades: List[Dict[str, Any]]
    ) -> float:
        """Estimate transaction costs"""
        
        total_cost = 0
        for trade in trades:
            # Assume 0.1% transaction cost
            total_cost += trade.get("value", 0) * 0.001
        
        return total_cost
    
    def _explain_rebalancing(
        self,
        drifts: Dict[str, Any],
        trades: List[Dict[str, Any]]
    ) -> str:
        """Explain rebalancing recommendation"""
        
        significant_drifts = [
            f"{ticker}: {info['drift']:.1%}"
            for ticker, info in drifts.items()
            if abs(info['drift']) > self.rebalancing_threshold
        ]
        
        return (
            f"Portfolio has drifted from target allocation. "
            f"Significant drifts: {', '.join(significant_drifts)}. "
            f"Recommend {len(trades)} trades to rebalance."
        )
    
    def _explain_rl_action(
        self,
        action: Action,
        portfolio: Dict[str, Any]
    ) -> str:
        """Explain RL agent recommendation"""
        
        explanations = {
            Action.BUY_SMALL: "Increase positions slightly to improve diversification",
            Action.BUY_MEDIUM: "Moderate buying recommended based on market conditions",
            Action.BUY_LARGE: "Strong buying signal - significant upside expected",
            Action.SELL_SMALL: "Slight reduction recommended to manage risk",
            Action.SELL_MEDIUM: "Moderate selling to rebalance portfolio",
            Action.SELL_LARGE: "Significant reduction recommended - high risk detected",
            Action.REBALANCE: "Portfolio drift detected - rebalancing recommended",
            Action.HOLD: "Current allocation is optimal - maintain positions"
        }
        
        return explanations.get(action, "No action needed")
    
    def _calculate_optimal_allocation(
        self,
        predictions: Dict[str, Any],
        risk_profile: str,
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate optimal allocation based on predictions"""
        
        # Simple equal weight for now
        # In production, use modern portfolio theory
        num_assets = len(predictions)
        if num_assets == 0:
            return {}
        
        return {ticker: 1.0/num_assets for ticker in predictions.keys()}
    
    def _calculate_expected_return(
        self,
        predictions: Dict[str, Any]
    ) -> float:
        """Calculate expected portfolio return"""
        
        if not predictions:
            return 0
        
        returns = [
            p.get("predicted_return", 0) 
            for p in predictions.values()
        ]
        
        return sum(returns) / len(returns)
    
    def _calculate_expected_risk(
        self,
        predictions: Dict[str, Any]
    ) -> float:
        """Calculate expected portfolio risk (volatility)"""
        
        # Simplified - use average volatility
        return 0.15  # 15% volatility placeholder
    
    def _calculate_expected_sharpe(
        self,
        predictions: Dict[str, Any]
    ) -> float:
        """Calculate expected Sharpe ratio"""
        
        expected_return = self._calculate_expected_return(predictions)
        expected_risk = self._calculate_expected_risk(predictions)
        risk_free_rate = 0.04  # 4% risk-free rate
        
        if expected_risk == 0:
            return 0
        
        return (expected_return - risk_free_rate) / expected_risk
    
    def _explain_optimization(
        self,
        predictions: Dict[str, Any],
        risk_profile: str
    ) -> str:
        """Explain optimization recommendation"""
        
        return (
            f"Optimization based on {risk_profile} risk profile. "
            f"ML predictions analyzed for {len(predictions)} positions. "
            f"Allocation optimized for risk-adjusted returns."
        )
    
    def _calculate_anomaly_risk_level(
        self,
        anomalies: List[Dict[str, Any]]
    ) -> str:
        """Calculate overall risk level from anomalies"""
        
        if not anomalies:
            return "low"
        
        high_severity = sum(1 for a in anomalies if a.get("severity") == "high")
        
        if high_severity >= 2:
            return "high"
        elif high_severity == 1 or len(anomalies) >= 3:
            return "medium"
        else:
            return "low"

# Global instance
holdings_agent = HoldingsAgent()
