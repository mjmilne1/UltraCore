"""
Alert Aggregates
Event-sourced aggregates for price, portfolio, and news alerts
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from ultracore.notifications.events import (
    PriceAlertCreated,
    PriceAlertTriggered,
    PortfolioAlertCreated,
    PortfolioAlertTriggered,
    NewsAlertCreated,
    NewsAlertTriggered,
    AlertPriority
)
from ultracore.notifications.event_publisher import get_notification_event_publisher


class PriceAlertAggregate:
    """
    Price Alert Aggregate
    
    Manages price alerts for securities
    Alert types: above, below, change_percent
    """
    
    def __init__(self, alert_id: str, tenant_id: str):
        self.alert_id = alert_id
        self.tenant_id = tenant_id
        self.client_id: Optional[str] = None
        self.symbol: Optional[str] = None
        self.alert_type: Optional[str] = None
        self.target_price: Optional[float] = None
        self.change_percent: Optional[float] = None
        self.current_price: Optional[float] = None
        self.is_active: bool = True
        self.triggered_count: int = 0
        self.created_at: Optional[datetime] = None
        self.last_triggered_at: Optional[datetime] = None
        
        self.uncommitted_events: List[Any] = []
        self.publisher = get_notification_event_publisher()
    
    def create_alert(
        self,
        user_id: str,
        client_id: str,
        symbol: str,
        alert_type: str,
        target_price: Optional[float] = None,
        change_percent: Optional[float] = None,
        current_price: float = 0.0
    ) -> None:
        """
        Create price alert
        
        Args:
            user_id: User creating alert
            client_id: Client ID
            symbol: Security symbol
            alert_type: above, below, change_percent
            target_price: Target price for above/below alerts
            change_percent: Change percentage for change_percent alerts
            current_price: Current price at creation
        """
        event = PriceAlertCreated(
            event_id=str(uuid4()),
            alert_id=self.alert_id,
            tenant_id=self.tenant_id,
            client_id=client_id,
            user_id=user_id,
            symbol=symbol,
            alert_type=alert_type,
            target_price=target_price,
            change_percent=change_percent,
            current_price=current_price,
            created_at=datetime.utcnow()
        )
        
        self._apply_price_alert_created(event)
        self.uncommitted_events.append(event)
    
    def trigger_alert(
        self,
        current_price: float,
        change_percent: Optional[float] = None
    ) -> None:
        """
        Trigger price alert
        
        Args:
            current_price: Current price that triggered alert
            change_percent: Price change percentage
        """
        event = PriceAlertTriggered(
            event_id=str(uuid4()),
            alert_id=self.alert_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            symbol=self.symbol,
            target_price=self.target_price,
            current_price=current_price,
            change_percent=change_percent,
            triggered_at=datetime.utcnow()
        )
        
        self._apply_price_alert_triggered(event)
        self.uncommitted_events.append(event)
    
    def _apply_price_alert_created(self, event: PriceAlertCreated) -> None:
        """Apply PriceAlertCreated event"""
        self.client_id = event.client_id
        self.symbol = event.symbol
        self.alert_type = event.alert_type
        self.target_price = event.target_price
        self.change_percent = event.change_percent
        self.current_price = event.current_price
        self.created_at = event.created_at
        self.is_active = True
    
    def _apply_price_alert_triggered(self, event: PriceAlertTriggered) -> None:
        """Apply PriceAlertTriggered event"""
        self.current_price = event.current_price
        self.triggered_count += 1
        self.last_triggered_at = event.triggered_at
    
    def commit(self) -> bool:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            success = self.publisher.publish_alert_event(
                event=event,
                aggregate_id=self.alert_id,
                tenant_id=self.tenant_id
            )
            if not success:
                return False
        
        self.uncommitted_events.clear()
        return True


class PortfolioAlertAggregate:
    """
    Portfolio Alert Aggregate
    
    Manages portfolio alerts
    Alert types: rebalancing_needed, risk_threshold, performance
    """
    
    def __init__(self, alert_id: str, tenant_id: str):
        self.alert_id = alert_id
        self.tenant_id = tenant_id
        self.client_id: Optional[str] = None
        self.portfolio_id: Optional[str] = None
        self.alert_type: Optional[str] = None
        self.threshold_value: Optional[float] = None
        self.is_active: bool = True
        self.triggered_count: int = 0
        self.created_at: Optional[datetime] = None
        self.last_triggered_at: Optional[datetime] = None
        
        self.uncommitted_events: List[Any] = []
        self.publisher = get_notification_event_publisher()
    
    def create_alert(
        self,
        user_id: str,
        client_id: str,
        portfolio_id: str,
        alert_type: str,
        threshold_value: Optional[float] = None
    ) -> None:
        """
        Create portfolio alert
        
        Args:
            user_id: User creating alert
            client_id: Client ID
            portfolio_id: Portfolio ID
            alert_type: rebalancing_needed, risk_threshold, performance
            threshold_value: Threshold value for alert
        """
        event = PortfolioAlertCreated(
            event_id=str(uuid4()),
            alert_id=self.alert_id,
            tenant_id=self.tenant_id,
            client_id=client_id,
            user_id=user_id,
            portfolio_id=portfolio_id,
            alert_type=alert_type,
            threshold_value=threshold_value,
            created_at=datetime.utcnow()
        )
        
        self._apply_portfolio_alert_created(event)
        self.uncommitted_events.append(event)
    
    def trigger_alert(
        self,
        current_value: float,
        details: Dict[str, Any]
    ) -> None:
        """
        Trigger portfolio alert
        
        Args:
            current_value: Current value that triggered alert
            details: Additional details about the alert
        """
        event = PortfolioAlertTriggered(
            event_id=str(uuid4()),
            alert_id=self.alert_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            portfolio_id=self.portfolio_id,
            alert_type=self.alert_type,
            current_value=current_value,
            threshold_value=self.threshold_value,
            details=details,
            triggered_at=datetime.utcnow()
        )
        
        self._apply_portfolio_alert_triggered(event)
        self.uncommitted_events.append(event)
    
    def _apply_portfolio_alert_created(self, event: PortfolioAlertCreated) -> None:
        """Apply PortfolioAlertCreated event"""
        self.client_id = event.client_id
        self.portfolio_id = event.portfolio_id
        self.alert_type = event.alert_type
        self.threshold_value = event.threshold_value
        self.created_at = event.created_at
        self.is_active = True
    
    def _apply_portfolio_alert_triggered(self, event: PortfolioAlertTriggered) -> None:
        """Apply PortfolioAlertTriggered event"""
        self.triggered_count += 1
        self.last_triggered_at = event.triggered_at
    
    def commit(self) -> bool:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            success = self.publisher.publish_alert_event(
                event=event,
                aggregate_id=self.alert_id,
                tenant_id=self.tenant_id
            )
            if not success:
                return False
        
        self.uncommitted_events.clear()
        return True


class NewsAlertAggregate:
    """
    News Alert Aggregate
    
    Manages news alerts for securities
    News types: earnings, announcements, regulatory
    """
    
    def __init__(self, alert_id: str, tenant_id: str):
        self.alert_id = alert_id
        self.tenant_id = tenant_id
        self.client_id: Optional[str] = None
        self.symbols: List[str] = []
        self.keywords: List[str] = []
        self.news_types: List[str] = []
        self.is_active: bool = True
        self.triggered_count: int = 0
        self.created_at: Optional[datetime] = None
        self.last_triggered_at: Optional[datetime] = None
        
        self.uncommitted_events: List[Any] = []
        self.publisher = get_notification_event_publisher()
    
    def create_alert(
        self,
        user_id: str,
        client_id: str,
        symbols: List[str],
        keywords: List[str],
        news_types: List[str]
    ) -> None:
        """
        Create news alert
        
        Args:
            user_id: User creating alert
            client_id: Client ID
            symbols: List of symbols to monitor
            keywords: Keywords to match
            news_types: Types of news to monitor
        """
        event = NewsAlertCreated(
            event_id=str(uuid4()),
            alert_id=self.alert_id,
            tenant_id=self.tenant_id,
            client_id=client_id,
            user_id=user_id,
            symbols=symbols,
            keywords=keywords,
            news_types=news_types,
            created_at=datetime.utcnow()
        )
        
        self._apply_news_alert_created(event)
        self.uncommitted_events.append(event)
    
    def trigger_alert(
        self,
        symbol: str,
        news_type: str,
        headline: str,
        summary: str,
        source: str,
        url: Optional[str] = None
    ) -> None:
        """
        Trigger news alert
        
        Args:
            symbol: Symbol related to news
            news_type: Type of news
            headline: News headline
            summary: News summary
            source: News source
            url: URL to full article
        """
        event = NewsAlertTriggered(
            event_id=str(uuid4()),
            alert_id=self.alert_id,
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            symbol=symbol,
            news_type=news_type,
            headline=headline,
            summary=summary,
            source=source,
            url=url,
            triggered_at=datetime.utcnow()
        )
        
        self._apply_news_alert_triggered(event)
        self.uncommitted_events.append(event)
    
    def _apply_news_alert_created(self, event: NewsAlertCreated) -> None:
        """Apply NewsAlertCreated event"""
        self.client_id = event.client_id
        self.symbols = event.symbols
        self.keywords = event.keywords
        self.news_types = event.news_types
        self.created_at = event.created_at
        self.is_active = True
    
    def _apply_news_alert_triggered(self, event: NewsAlertTriggered) -> None:
        """Apply NewsAlertTriggered event"""
        self.triggered_count += 1
        self.last_triggered_at = event.triggered_at
    
    def commit(self) -> bool:
        """Commit uncommitted events to event store"""
        for event in self.uncommitted_events:
            success = self.publisher.publish_alert_event(
                event=event,
                aggregate_id=self.alert_id,
                tenant_id=self.tenant_id
            )
            if not success:
                return False
        
        self.uncommitted_events.clear()
        return True
