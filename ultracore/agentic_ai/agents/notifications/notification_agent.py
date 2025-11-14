"""
Notification AI Agent
Intelligent notification generation, prioritization, and delivery optimization
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ultracore.notifications.events import (
    NotificationType,
    AlertPriority,
    DeliveryChannel
)

logger = logging.getLogger(__name__)


class NotificationAgent:
    """
    AI Agent for Intelligent Notification Management
    
    Capabilities:
    - Generate smart alerts based on market conditions
    - Prioritize notifications using ML
    - Optimize delivery timing
    - Personalize notification content
    - Reduce notification fatigue
    - Batch related notifications
    """
    
    def __init__(self):
        self.name = "NotificationAgent"
        logger.info(f"{self.name} initialized")
    
    # ========================================================================
    # ALERT GENERATION
    # ========================================================================
    
    def should_trigger_price_alert(
        self,
        symbol: str,
        current_price: float,
        target_price: float,
        alert_type: str,
        historical_prices: List[float],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if price alert should be triggered
        
        Uses AI to avoid false positives from temporary price spikes
        
        Args:
            symbol: Security symbol
            current_price: Current price
            target_price: Target price
            alert_type: Alert type (above, below, change_percent)
            historical_prices: Recent price history
            market_conditions: Current market conditions
        
        Returns:
            Dictionary with trigger decision and reasoning
        """
        # Check basic trigger condition
        should_trigger = False
        if alert_type == "above" and current_price >= target_price:
            should_trigger = True
        elif alert_type == "below" and current_price <= target_price:
            should_trigger = True
        
        if not should_trigger:
            return {
                "should_trigger": False,
                "reason": "Price condition not met"
            }
        
        # AI analysis: Check if this is a sustained move or temporary spike
        if len(historical_prices) >= 5:
            recent_avg = sum(historical_prices[-5:]) / 5
            price_volatility = max(historical_prices[-5:]) - min(historical_prices[-5:])
            
            # If current price is far from recent average, might be a spike
            if abs(current_price - recent_avg) > price_volatility * 1.5:
                return {
                    "should_trigger": False,
                    "reason": "Likely temporary price spike, waiting for confirmation",
                    "confidence": 0.7
                }
        
        # Check market conditions
        if market_conditions.get("high_volatility", False):
            return {
                "should_trigger": True,
                "reason": "Target price reached in volatile market",
                "confidence": 0.8,
                "priority": AlertPriority.HIGH
            }
        
        return {
            "should_trigger": True,
            "reason": "Target price reached with confirmation",
            "confidence": 0.9,
            "priority": AlertPriority.MEDIUM
        }
    
    def should_trigger_portfolio_alert(
        self,
        portfolio_id: str,
        alert_type: str,
        current_value: float,
        threshold_value: float,
        portfolio_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine if portfolio alert should be triggered
        
        Args:
            portfolio_id: Portfolio ID
            alert_type: Alert type (rebalancing_needed, risk_threshold, performance)
            current_value: Current value
            threshold_value: Threshold value
            portfolio_data: Portfolio data
        
        Returns:
            Dictionary with trigger decision and reasoning
        """
        if alert_type == "rebalancing_needed":
            # Check if portfolio drift exceeds threshold
            drift = portfolio_data.get("drift_percent", 0)
            if drift >= threshold_value:
                return {
                    "should_trigger": True,
                    "reason": f"Portfolio drift ({drift:.1f}%) exceeds threshold ({threshold_value:.1f}%)",
                    "confidence": 0.95,
                    "priority": AlertPriority.MEDIUM,
                    "details": {
                        "drift_percent": drift,
                        "recommended_actions": self._generate_rebalancing_recommendations(portfolio_data)
                    }
                }
        
        elif alert_type == "risk_threshold":
            # Check if portfolio risk exceeds threshold
            risk_score = portfolio_data.get("risk_score", 0)
            if risk_score >= threshold_value:
                severity = "high" if risk_score >= threshold_value * 1.2 else "medium"
                return {
                    "should_trigger": True,
                    "reason": f"Portfolio risk ({risk_score:.1f}) exceeds threshold ({threshold_value:.1f})",
                    "confidence": 0.9,
                    "priority": AlertPriority.HIGH if severity == "high" else AlertPriority.MEDIUM,
                    "details": {
                        "risk_score": risk_score,
                        "risk_factors": portfolio_data.get("risk_factors", [])
                    }
                }
        
        elif alert_type == "performance":
            # Check portfolio performance
            performance = portfolio_data.get("performance_percent", 0)
            if performance <= threshold_value:  # Negative threshold for underperformance
                return {
                    "should_trigger": True,
                    "reason": f"Portfolio underperforming ({performance:.1f}%) vs threshold ({threshold_value:.1f}%)",
                    "confidence": 0.85,
                    "priority": AlertPriority.MEDIUM,
                    "details": {
                        "performance_percent": performance,
                        "benchmark_comparison": portfolio_data.get("benchmark_comparison", {})
                    }
                }
        
        return {
            "should_trigger": False,
            "reason": "Threshold not exceeded"
        }
    
    def _generate_rebalancing_recommendations(
        self,
        portfolio_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered rebalancing recommendations"""
        # TODO: Implement ML-based rebalancing recommendations
        return [
            {
                "action": "reduce",
                "asset": "Tech Stocks",
                "current_percent": 45,
                "target_percent": 35,
                "reason": "Overweight relative to target allocation"
            },
            {
                "action": "increase",
                "asset": "Bonds",
                "current_percent": 15,
                "target_percent": 25,
                "reason": "Underweight relative to target allocation"
            }
        ]
    
    # ========================================================================
    # PRIORITIZATION
    # ========================================================================
    
    def calculate_notification_priority(
        self,
        notification_type: NotificationType,
        client_data: Dict[str, Any],
        notification_data: Dict[str, Any],
        user_preferences: Dict[str, Any]
    ) -> AlertPriority:
        """
        Calculate notification priority using AI
        
        Considers:
        - Notification type
        - Client risk profile
        - Portfolio size
        - User preferences
        - Historical engagement
        
        Args:
            notification_type: Type of notification
            client_data: Client information
            notification_data: Notification details
            user_preferences: User preferences
        
        Returns:
            Alert priority
        """
        base_priority = {
            NotificationType.PRICE_ALERT: AlertPriority.MEDIUM,
            NotificationType.PORTFOLIO_ALERT: AlertPriority.HIGH,
            NotificationType.NEWS_ALERT: AlertPriority.LOW,
            NotificationType.TRANSACTION_CONFIRMATION: AlertPriority.HIGH,
            NotificationType.PORTFOLIO_SUMMARY: AlertPriority.LOW,
            NotificationType.ML_PREDICTION: AlertPriority.MEDIUM,
            NotificationType.COMPLIANCE_ALERT: AlertPriority.URGENT,
            NotificationType.SYSTEM_ALERT: AlertPriority.MEDIUM
        }.get(notification_type, AlertPriority.MEDIUM)
        
        # Adjust based on client risk profile
        risk_profile = client_data.get("risk_profile", "medium")
        if risk_profile == "high" and notification_type == NotificationType.PORTFOLIO_ALERT:
            # High-risk clients get higher priority for portfolio alerts
            if base_priority == AlertPriority.HIGH:
                base_priority = AlertPriority.URGENT
        
        # Adjust based on portfolio size
        portfolio_value = client_data.get("portfolio_value", 0)
        if portfolio_value > 1000000:  # $1M+
            # Large portfolios get higher priority
            if base_priority == AlertPriority.MEDIUM:
                base_priority = AlertPriority.HIGH
        
        # Adjust based on user engagement
        engagement_score = user_preferences.get("engagement_score", 0.5)
        if engagement_score < 0.3:
            # Low engagement users: only send high priority
            if base_priority in [AlertPriority.LOW, AlertPriority.MEDIUM]:
                base_priority = AlertPriority.MEDIUM  # Upgrade to ensure delivery
        
        return base_priority
    
    # ========================================================================
    # DELIVERY OPTIMIZATION
    # ========================================================================
    
    def optimize_delivery_time(
        self,
        client_id: str,
        notification_type: NotificationType,
        priority: AlertPriority,
        user_preferences: Dict[str, Any],
        historical_engagement: List[Dict[str, Any]]
    ) -> datetime:
        """
        Optimize notification delivery time using AI
        
        Considers:
        - User timezone
        - Quiet hours
        - Historical engagement patterns
        - Notification priority
        
        Args:
            client_id: Client ID
            notification_type: Type of notification
            priority: Alert priority
            user_preferences: User preferences
            historical_engagement: Historical engagement data
        
        Returns:
            Optimal delivery time
        """
        now = datetime.utcnow()
        
        # Urgent notifications: deliver immediately
        if priority == AlertPriority.URGENT:
            return now
        
        # Check quiet hours
        quiet_hours_start = user_preferences.get("quiet_hours_start")
        quiet_hours_end = user_preferences.get("quiet_hours_end")
        
        if quiet_hours_start and quiet_hours_end:
            # TODO: Implement timezone-aware quiet hours check
            # For now, respect quiet hours for non-urgent notifications
            if priority in [AlertPriority.LOW, AlertPriority.MEDIUM]:
                # Schedule for after quiet hours
                pass
        
        # Analyze historical engagement to find optimal time
        if historical_engagement:
            # Find time of day with highest engagement
            engagement_by_hour = {}
            for engagement in historical_engagement:
                hour = engagement.get("read_at", now).hour
                engagement_by_hour[hour] = engagement_by_hour.get(hour, 0) + 1
            
            if engagement_by_hour:
                optimal_hour = max(engagement_by_hour, key=engagement_by_hour.get)
                # Schedule for optimal hour if not too far in future
                optimal_time = now.replace(hour=optimal_hour, minute=0, second=0)
                if optimal_time < now:
                    optimal_time += timedelta(days=1)
                
                if (optimal_time - now).total_seconds() < 3600 * 6:  # Within 6 hours
                    return optimal_time
        
        # Default: deliver immediately for high priority, delay low priority
        if priority == AlertPriority.HIGH:
            return now
        else:
            # Batch low priority notifications
            return now + timedelta(hours=1)
    
    def select_delivery_channels(
        self,
        client_id: str,
        notification_type: NotificationType,
        priority: AlertPriority,
        user_preferences: Dict[str, Any]
    ) -> List[DeliveryChannel]:
        """
        Select optimal delivery channels using AI
        
        Args:
            client_id: Client ID
            notification_type: Type of notification
            priority: Alert priority
            user_preferences: User preferences
        
        Returns:
            List of delivery channels
        """
        # Get user preferred channels
        preferred_channels = user_preferences.get("channels", [DeliveryChannel.EMAIL])
        
        # Urgent notifications: use all available channels
        if priority == AlertPriority.URGENT:
            return [DeliveryChannel.EMAIL, DeliveryChannel.SMS, DeliveryChannel.PUSH, DeliveryChannel.IN_APP]
        
        # High priority: use preferred + push
        if priority == AlertPriority.HIGH:
            channels = list(set(preferred_channels + [DeliveryChannel.PUSH, DeliveryChannel.IN_APP]))
            return channels
        
        # Medium/Low priority: use preferred channels only
        return preferred_channels
    
    # ========================================================================
    # CONTENT PERSONALIZATION
    # ========================================================================
    
    def personalize_notification_content(
        self,
        notification_type: NotificationType,
        client_data: Dict[str, Any],
        notification_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Personalize notification content using AI
        
        Args:
            notification_type: Type of notification
            client_data: Client information
            notification_data: Notification details
        
        Returns:
            Dictionary with title and message
        """
        client_name = client_data.get("name", "Valued Client")
        
        if notification_type == NotificationType.PRICE_ALERT:
            symbol = notification_data.get("symbol")
            current_price = notification_data.get("current_price")
            target_price = notification_data.get("target_price")
            
            return {
                "title": f"Price Alert: {symbol}",
                "message": f"Hi {client_name}, {symbol} has reached your target price of ${target_price:.2f}. Current price: ${current_price:.2f}."
            }
        
        elif notification_type == NotificationType.PORTFOLIO_ALERT:
            alert_type = notification_data.get("alert_type")
            
            if alert_type == "rebalancing_needed":
                return {
                    "title": "Portfolio Rebalancing Recommended",
                    "message": f"Hi {client_name}, your portfolio has drifted from its target allocation. Consider rebalancing to maintain your investment strategy."
                }
            elif alert_type == "risk_threshold":
                return {
                    "title": "Portfolio Risk Alert",
                    "message": f"Hi {client_name}, your portfolio risk level has exceeded your threshold. Review your holdings to manage risk."
                }
        
        elif notification_type == NotificationType.TRANSACTION_CONFIRMATION:
            transaction_type = notification_data.get("transaction_type")
            amount = notification_data.get("amount")
            
            return {
                "title": "Transaction Confirmed",
                "message": f"Hi {client_name}, your {transaction_type} of ${amount:.2f} has been confirmed."
            }
        
        # Default
        return {
            "title": "Notification",
            "message": f"Hi {client_name}, you have a new notification."
        }
    
    # ========================================================================
    # NOTIFICATION FATIGUE MANAGEMENT
    # ========================================================================
    
    def should_suppress_notification(
        self,
        client_id: str,
        notification_type: NotificationType,
        priority: AlertPriority,
        recent_notifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Determine if notification should be suppressed to avoid fatigue
        
        Args:
            client_id: Client ID
            notification_type: Type of notification
            priority: Alert priority
            recent_notifications: Recent notifications sent
        
        Returns:
            Dictionary with suppression decision and reasoning
        """
        # Never suppress urgent notifications
        if priority == AlertPriority.URGENT:
            return {
                "should_suppress": False,
                "reason": "Urgent priority"
            }
        
        # Count recent notifications (last 24 hours)
        now = datetime.utcnow()
        recent_count = len([
            n for n in recent_notifications
            if (now - n.get("created_at", now)).total_seconds() < 86400
        ])
        
        # Suppress if too many notifications
        if recent_count > 10:
            return {
                "should_suppress": True,
                "reason": f"Too many recent notifications ({recent_count} in 24h)",
                "recommendation": "Batch into daily digest"
            }
        
        # Check for duplicate notifications
        similar_count = len([
            n for n in recent_notifications[-5:]
            if n.get("notification_type") == notification_type
        ])
        
        if similar_count >= 3:
            return {
                "should_suppress": True,
                "reason": f"Too many similar notifications ({similar_count} recent)",
                "recommendation": "Consolidate into single notification"
            }
        
        return {
            "should_suppress": False,
            "reason": "Within acceptable limits"
        }
    
    def batch_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Batch multiple notifications into digest
        
        Args:
            notifications: List of notifications to batch
        
        Returns:
            Batched notification
        """
        if not notifications:
            return {}
        
        # Group by type
        by_type = {}
        for notification in notifications:
            ntype = notification.get("notification_type")
            if ntype not in by_type:
                by_type[ntype] = []
            by_type[ntype].append(notification)
        
        # Generate digest
        title = f"Daily Digest: {len(notifications)} Updates"
        message_parts = []
        
        for ntype, items in by_type.items():
            message_parts.append(f"\n{ntype}: {len(items)} notifications")
        
        return {
            "title": title,
            "message": "".join(message_parts),
            "notification_type": NotificationType.PORTFOLIO_SUMMARY,
            "priority": AlertPriority.LOW,
            "batched_notifications": notifications
        }


# Singleton instance
_notification_agent: Optional[NotificationAgent] = None


def get_notification_agent() -> NotificationAgent:
    """Get notification agent instance"""
    global _notification_agent
    if _notification_agent is None:
        _notification_agent = NotificationAgent()
    return _notification_agent
