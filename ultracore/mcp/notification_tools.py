"""
Notification MCP Tools
Model Context Protocol tools for notification operations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ultracore.notifications.events import (
    NotificationType,
    AlertPriority,
    DeliveryChannel,
    PriceAlertCreated,
    PortfolioAlertCreated,
    NewsAlertCreated,
    NotificationCreated,
    NotificationPreferenceUpdated
)
from ultracore.notifications.event_publisher import NotificationEventPublisher
from ultracore.agentic_ai.agents.notifications import get_notification_agent
from ultracore.ml.notifications import get_engagement_model, get_preference_learning_model

logger = logging.getLogger(__name__)


class NotificationTools:
    """
    MCP Tools for Notification Operations
    
    Provides tools for:
    - Creating alerts
    - Sending notifications
    - Managing preferences
    - Multi-channel delivery
    - Analytics and reporting
    """
    
    def __init__(self):
        self.event_publisher = NotificationEventPublisher()
        self.notification_agent = get_notification_agent()
        self.engagement_model = get_engagement_model()
        self.preference_model = get_preference_learning_model()
        logger.info("NotificationTools initialized")
    
    # ========================================================================
    # ALERT CREATION TOOLS
    # ========================================================================
    
    def create_price_alert(
        self,
        tenant_id: str,
        client_id: str,
        symbol: str,
        target_price: float,
        alert_type: str,  # "above", "below", "change_percent"
        threshold_percent: Optional[float] = None,
        expiry_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create price alert
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            symbol: Security symbol
            target_price: Target price
            alert_type: Alert type
            threshold_percent: Optional threshold percentage for change alerts
            expiry_date: Optional expiry date (ISO format)
        
        Returns:
            Alert creation result
        """
        try:
            alert_id = f"price_alert_{tenant_id}_{client_id}_{symbol}_{datetime.utcnow().timestamp()}"
            
            event = PriceAlertCreated(
                tenant_id=tenant_id,
                alert_id=alert_id,
                client_id=client_id,
                symbol=symbol,
                target_price=target_price,
                alert_type=alert_type,
                threshold_percent=threshold_percent,
                expiry_date=datetime.fromisoformat(expiry_date) if expiry_date else None,
                created_at=datetime.utcnow()
            )
            
            self.event_publisher.publish_event(event)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "message": f"Price alert created for {symbol} at ${target_price}"
            }
        
        except Exception as e:
            logger.error(f"Error creating price alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_portfolio_alert(
        self,
        tenant_id: str,
        client_id: str,
        portfolio_id: str,
        alert_type: str,  # "rebalancing_needed", "risk_threshold", "performance"
        threshold_value: float,
        threshold_type: str = "percent"
    ) -> Dict[str, Any]:
        """
        Create portfolio alert
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            portfolio_id: Portfolio ID
            alert_type: Alert type
            threshold_value: Threshold value
            threshold_type: Threshold type (percent, absolute)
        
        Returns:
            Alert creation result
        """
        try:
            alert_id = f"portfolio_alert_{tenant_id}_{client_id}_{portfolio_id}_{datetime.utcnow().timestamp()}"
            
            event = PortfolioAlertCreated(
                tenant_id=tenant_id,
                alert_id=alert_id,
                client_id=client_id,
                portfolio_id=portfolio_id,
                alert_type=alert_type,
                threshold_value=threshold_value,
                threshold_type=threshold_type,
                created_at=datetime.utcnow()
            )
            
            self.event_publisher.publish_event(event)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "message": f"Portfolio alert created for {alert_type}"
            }
        
        except Exception as e:
            logger.error(f"Error creating portfolio alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_news_alert(
        self,
        tenant_id: str,
        client_id: str,
        symbols: List[str],
        keywords: Optional[List[str]] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create news alert
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            symbols: List of symbols to monitor
            keywords: Optional keywords to filter
            categories: Optional categories (earnings, announcements, etc.)
        
        Returns:
            Alert creation result
        """
        try:
            alert_id = f"news_alert_{tenant_id}_{client_id}_{datetime.utcnow().timestamp()}"
            
            event = NewsAlertCreated(
                tenant_id=tenant_id,
                alert_id=alert_id,
                client_id=client_id,
                symbols=symbols,
                keywords=keywords or [],
                categories=categories or [],
                created_at=datetime.utcnow()
            )
            
            self.event_publisher.publish_event(event)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "message": f"News alert created for {len(symbols)} symbols"
            }
        
        except Exception as e:
            logger.error(f"Error creating news alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ========================================================================
    # NOTIFICATION SENDING TOOLS
    # ========================================================================
    
    def send_notification(
        self,
        tenant_id: str,
        client_id: str,
        notification_type: str,
        title: str,
        message: str,
        priority: str = "medium",
        channels: Optional[List[str]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notification to client
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level (low, medium, high, urgent)
            channels: Optional list of delivery channels
            data: Optional additional data
        
        Returns:
            Notification sending result
        """
        try:
            notification_id = f"notification_{tenant_id}_{client_id}_{datetime.utcnow().timestamp()}"
            
            # Convert string enums
            ntype = NotificationType[notification_type.upper()]
            npriority = AlertPriority[priority.upper()]
            nchannels = [DeliveryChannel[c.upper()] for c in (channels or ["EMAIL", "IN_APP"])]
            
            event = NotificationCreated(
                tenant_id=tenant_id,
                notification_id=notification_id,
                client_id=client_id,
                notification_type=ntype,
                title=title,
                message=message,
                priority=npriority,
                channels=nchannels,
                data=data or {},
                created_at=datetime.utcnow()
            )
            
            self.event_publisher.publish_event(event)
            
            return {
                "success": True,
                "notification_id": notification_id,
                "message": f"Notification sent via {len(nchannels)} channels"
            }
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_transaction_confirmation(
        self,
        tenant_id: str,
        client_id: str,
        transaction_id: str,
        transaction_type: str,
        amount: float,
        currency: str,
        symbol: Optional[str] = None,
        quantity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Send transaction confirmation notification
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            transaction_id: Transaction ID
            transaction_type: Type of transaction (buy, sell, deposit, withdrawal)
            amount: Transaction amount
            currency: Currency code
            symbol: Optional security symbol
            quantity: Optional quantity
        
        Returns:
            Notification sending result
        """
        title = f"Transaction Confirmed: {transaction_type.title()}"
        
        if symbol and quantity:
            message = f"Your {transaction_type} of {quantity} shares of {symbol} for {currency} ${amount:,.2f} has been confirmed."
        else:
            message = f"Your {transaction_type} of {currency} ${amount:,.2f} has been confirmed."
        
        return self.send_notification(
            tenant_id=tenant_id,
            client_id=client_id,
            notification_type="transaction_confirmation",
            title=title,
            message=message,
            priority="high",
            channels=["EMAIL", "SMS", "IN_APP"],
            data={
                "transaction_id": transaction_id,
                "transaction_type": transaction_type,
                "amount": amount,
                "currency": currency,
                "symbol": symbol,
                "quantity": quantity
            }
        )
    
    def send_portfolio_summary(
        self,
        tenant_id: str,
        client_id: str,
        portfolio_id: str,
        period: str,  # "daily", "weekly", "monthly"
        summary_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send portfolio summary notification
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            portfolio_id: Portfolio ID
            period: Summary period
            summary_data: Summary data
        
        Returns:
            Notification sending result
        """
        title = f"{period.title()} Portfolio Summary"
        
        total_value = summary_data.get("total_value", 0)
        change_percent = summary_data.get("change_percent", 0)
        change_direction = "up" if change_percent >= 0 else "down"
        
        message = f"Your portfolio is {change_direction} {abs(change_percent):.2f}% this {period}. Current value: ${total_value:,.2f}"
        
        return self.send_notification(
            tenant_id=tenant_id,
            client_id=client_id,
            notification_type="portfolio_summary",
            title=title,
            message=message,
            priority="low",
            channels=["EMAIL", "IN_APP"],
            data={
                "portfolio_id": portfolio_id,
                "period": period,
                **summary_data
            }
        )
    
    def send_ml_prediction(
        self,
        tenant_id: str,
        client_id: str,
        prediction_type: str,
        symbol: Optional[str] = None,
        prediction_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send ML prediction notification
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            prediction_type: Type of prediction
            symbol: Optional symbol
            prediction_data: Prediction data
        
        Returns:
            Notification sending result
        """
        title = f"AI Prediction: {prediction_type.replace('_', ' ').title()}"
        
        # Generate message based on prediction type
        if symbol:
            message = f"Our AI model has a new prediction for {symbol}. Check your app for details."
        else:
            message = f"Our AI model has generated a new {prediction_type} prediction. Check your app for details."
        
        return self.send_notification(
            tenant_id=tenant_id,
            client_id=client_id,
            notification_type="ml_prediction",
            title=title,
            message=message,
            priority="medium",
            channels=["EMAIL", "PUSH", "IN_APP"],
            data={
                "prediction_type": prediction_type,
                "symbol": symbol,
                **(prediction_data or {})
            }
        )
    
    # ========================================================================
    # PREFERENCE MANAGEMENT TOOLS
    # ========================================================================
    
    def update_notification_preferences(
        self,
        tenant_id: str,
        client_id: str,
        notification_type: str,
        enabled: bool,
        channels: Optional[List[str]] = None,
        frequency: Optional[str] = None,
        quiet_hours_start: Optional[str] = None,
        quiet_hours_end: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update notification preferences
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            notification_type: Type of notification
            enabled: Whether notifications are enabled
            channels: Optional list of delivery channels
            frequency: Optional frequency (immediate, hourly, daily)
            quiet_hours_start: Optional quiet hours start (HH:MM)
            quiet_hours_end: Optional quiet hours end (HH:MM)
        
        Returns:
            Update result
        """
        try:
            preference_id = f"pref_{tenant_id}_{client_id}_{notification_type}"
            
            ntype = NotificationType[notification_type.upper()]
            nchannels = [DeliveryChannel[c.upper()] for c in (channels or ["EMAIL"])] if channels else None
            
            event = NotificationPreferenceUpdated(
                tenant_id=tenant_id,
                preference_id=preference_id,
                client_id=client_id,
                notification_type=ntype,
                enabled=enabled,
                channels=nchannels,
                frequency=frequency,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
                updated_at=datetime.utcnow()
            )
            
            self.event_publisher.publish_event(event)
            
            return {
                "success": True,
                "preference_id": preference_id,
                "message": "Notification preferences updated"
            }
        
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_recommended_preferences(
        self,
        tenant_id: str,
        client_id: str,
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get AI-recommended notification preferences
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            historical_data: Historical engagement data
        
        Returns:
            Recommended preferences
        """
        try:
            recommendations = self.preference_model.recommend_preferences(
                user_id=client_id,
                historical_data=historical_data
            )
            
            return {
                "success": True,
                "recommendations": recommendations
            }
        
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ========================================================================
    # ANALYTICS TOOLS
    # ========================================================================
    
    def predict_engagement(
        self,
        tenant_id: str,
        client_id: str,
        notification_data: Dict[str, Any],
        user_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict notification engagement probability
        
        Args:
            tenant_id: Tenant ID
            client_id: Client ID
            notification_data: Notification details
            user_data: User profile data
            historical_data: Historical engagement data
        
        Returns:
            Engagement prediction
        """
        try:
            prediction = self.engagement_model.predict_engagement(
                notification_data=notification_data,
                user_data=user_data,
                historical_data=historical_data
            )
            
            return {
                "success": True,
                "prediction": prediction
            }
        
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_notification_statistics(
        self,
        tenant_id: str,
        client_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get notification statistics
        
        Args:
            tenant_id: Tenant ID
            client_id: Optional client ID filter
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
        
        Returns:
            Statistics
        """
        # TODO: Implement statistics query
        return {
            "success": True,
            "statistics": {
                "total_sent": 0,
                "total_delivered": 0,
                "total_read": 0,
                "delivery_rate": 0.0,
                "read_rate": 0.0,
                "by_type": {},
                "by_channel": {}
            }
        }


# Singleton instance
_notification_tools: Optional[NotificationTools] = None


def get_notification_tools() -> NotificationTools:
    """Get notification tools instance"""
    global _notification_tools
    if _notification_tools is None:
        _notification_tools = NotificationTools()
    return _notification_tools


# MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "create_price_alert",
        "description": "Create a price alert for a security",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "symbol": {"type": "string"},
                "target_price": {"type": "number"},
                "alert_type": {"type": "string", "enum": ["above", "below", "change_percent"]},
                "threshold_percent": {"type": "number"},
                "expiry_date": {"type": "string"}
            },
            "required": ["tenant_id", "client_id", "symbol", "target_price", "alert_type"]
        }
    },
    {
        "name": "create_portfolio_alert",
        "description": "Create a portfolio alert",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "portfolio_id": {"type": "string"},
                "alert_type": {"type": "string", "enum": ["rebalancing_needed", "risk_threshold", "performance"]},
                "threshold_value": {"type": "number"},
                "threshold_type": {"type": "string", "enum": ["percent", "absolute"]}
            },
            "required": ["tenant_id", "client_id", "portfolio_id", "alert_type", "threshold_value"]
        }
    },
    {
        "name": "send_notification",
        "description": "Send a notification to a client",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "notification_type": {"type": "string"},
                "title": {"type": "string"},
                "message": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "channels": {"type": "array", "items": {"type": "string"}},
                "data": {"type": "object"}
            },
            "required": ["tenant_id", "client_id", "notification_type", "title", "message"]
        }
    },
    {
        "name": "send_transaction_confirmation",
        "description": "Send a transaction confirmation notification",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "transaction_id": {"type": "string"},
                "transaction_type": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "symbol": {"type": "string"},
                "quantity": {"type": "number"}
            },
            "required": ["tenant_id", "client_id", "transaction_id", "transaction_type", "amount", "currency"]
        }
    },
    {
        "name": "update_notification_preferences",
        "description": "Update notification preferences for a client",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "notification_type": {"type": "string"},
                "enabled": {"type": "boolean"},
                "channels": {"type": "array", "items": {"type": "string"}},
                "frequency": {"type": "string"},
                "quiet_hours_start": {"type": "string"},
                "quiet_hours_end": {"type": "string"}
            },
            "required": ["tenant_id", "client_id", "notification_type", "enabled"]
        }
    },
    {
        "name": "get_recommended_preferences",
        "description": "Get AI-recommended notification preferences based on user behavior",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "historical_data": {"type": "array"}
            },
            "required": ["tenant_id", "client_id", "historical_data"]
        }
    },
    {
        "name": "predict_engagement",
        "description": "Predict notification engagement probability using ML",
        "parameters": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "client_id": {"type": "string"},
                "notification_data": {"type": "object"},
                "user_data": {"type": "object"},
                "historical_data": {"type": "array"}
            },
            "required": ["tenant_id", "client_id", "notification_data", "user_data", "historical_data"]
        }
    }
]
