"""
Notification Events
Kafka event schemas for notification system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class NotificationType(str, Enum):
    """Notification types"""
    PRICE_ALERT = "price_alert"
    PORTFOLIO_ALERT = "portfolio_alert"
    NEWS_ALERT = "news_alert"
    TRANSACTION_CONFIRMATION = "transaction_confirmation"
    PORTFOLIO_SUMMARY = "portfolio_summary"
    ML_PREDICTION = "ml_prediction"
    COMPLIANCE_ALERT = "compliance_alert"
    SYSTEM_ALERT = "system_alert"


class AlertPriority(str, Enum):
    """Alert priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class DeliveryStatus(str, Enum):
    """Delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    READ = "read"


# ============================================================================
# ALERT EVENTS
# ============================================================================

@dataclass
class PriceAlertCreated:
    """Price alert created event"""
    event_id: str
    alert_id: str
    tenant_id: str
    client_id: str
    user_id: str
    symbol: str
    alert_type: str  # above, below, change_percent
    target_price: Optional[float]
    change_percent: Optional[float]
    current_price: float
    created_at: datetime
    
    @property
    def event_type(self) -> str:
        return "PriceAlertCreated"


@dataclass
class PriceAlertTriggered:
    """Price alert triggered event"""
    event_id: str
    alert_id: str
    tenant_id: str
    client_id: str
    symbol: str
    target_price: Optional[float]
    current_price: float
    change_percent: Optional[float]
    triggered_at: datetime
    
    @property
    def event_type(self) -> str:
        return "PriceAlertTriggered"


@dataclass
class PortfolioAlertCreated:
    """Portfolio alert created event"""
    event_id: str
    alert_id: str
    tenant_id: str
    client_id: str
    user_id: str
    portfolio_id: str
    alert_type: str  # rebalancing_needed, risk_threshold, performance
    threshold_value: Optional[float]
    created_at: datetime
    
    @property
    def event_type(self) -> str:
        return "PortfolioAlertCreated"


@dataclass
class PortfolioAlertTriggered:
    """Portfolio alert triggered event"""
    event_id: str
    alert_id: str
    tenant_id: str
    client_id: str
    portfolio_id: str
    alert_type: str
    current_value: float
    threshold_value: Optional[float]
    details: Dict[str, Any]
    triggered_at: datetime
    
    @property
    def event_type(self) -> str:
        return "PortfolioAlertTriggered"


@dataclass
class NewsAlertCreated:
    """News alert created event"""
    event_id: str
    alert_id: str
    tenant_id: str
    client_id: str
    user_id: str
    symbols: List[str]
    keywords: List[str]
    news_types: List[str]  # earnings, announcements, regulatory
    created_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NewsAlertCreated"


@dataclass
class NewsAlertTriggered:
    """News alert triggered event"""
    event_id: str
    alert_id: str
    tenant_id: str
    client_id: str
    symbol: str
    news_type: str
    headline: str
    summary: str
    source: str
    url: Optional[str]
    triggered_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NewsAlertTriggered"


# ============================================================================
# NOTIFICATION EVENTS
# ============================================================================

@dataclass
class NotificationCreated:
    """Notification created event"""
    event_id: str
    notification_id: str
    tenant_id: str
    client_id: str
    notification_type: NotificationType
    priority: AlertPriority
    title: str
    message: str
    data: Dict[str, Any]
    channels: List[DeliveryChannel]
    created_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationCreated"


@dataclass
class NotificationScheduled:
    """Notification scheduled for delivery"""
    event_id: str
    notification_id: str
    tenant_id: str
    client_id: str
    scheduled_for: datetime
    channels: List[DeliveryChannel]
    scheduled_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationScheduled"


@dataclass
class NotificationSent:
    """Notification sent event"""
    event_id: str
    notification_id: str
    tenant_id: str
    client_id: str
    channel: DeliveryChannel
    recipient: str
    sent_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationSent"


@dataclass
class NotificationDelivered:
    """Notification delivered event"""
    event_id: str
    notification_id: str
    tenant_id: str
    client_id: str
    channel: DeliveryChannel
    delivered_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationDelivered"


@dataclass
class NotificationRead:
    """Notification read event"""
    event_id: str
    notification_id: str
    tenant_id: str
    client_id: str
    read_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationRead"


@dataclass
class NotificationFailed:
    """Notification delivery failed event"""
    event_id: str
    notification_id: str
    tenant_id: str
    client_id: str
    channel: DeliveryChannel
    error_code: str
    error_message: str
    failed_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationFailed"


# ============================================================================
# PREFERENCE EVENTS
# ============================================================================

@dataclass
class NotificationPreferenceSet:
    """Notification preference set event"""
    event_id: str
    preference_id: str
    tenant_id: str
    client_id: str
    user_id: str
    notification_type: NotificationType
    enabled: bool
    channels: List[DeliveryChannel]
    quiet_hours_start: Optional[str]  # HH:MM
    quiet_hours_end: Optional[str]    # HH:MM
    frequency: str  # immediate, daily_digest, weekly_digest
    set_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationPreferenceSet"


@dataclass
class NotificationPreferenceUpdated:
    """Notification preference updated event"""
    event_id: str
    preference_id: str
    tenant_id: str
    client_id: str
    user_id: str
    changes: Dict[str, Any]
    updated_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationPreferenceUpdated"


# ============================================================================
# SUMMARY EVENTS
# ============================================================================

@dataclass
class PortfolioSummaryGenerated:
    """Portfolio summary generated event"""
    event_id: str
    summary_id: str
    tenant_id: str
    client_id: str
    portfolio_id: str
    period: str  # daily, weekly, monthly
    start_date: datetime
    end_date: datetime
    summary_data: Dict[str, Any]
    generated_at: datetime
    
    @property
    def event_type(self) -> str:
        return "PortfolioSummaryGenerated"


@dataclass
class MLPredictionGenerated:
    """ML prediction generated event"""
    event_id: str
    prediction_id: str
    tenant_id: str
    client_id: str
    prediction_type: str  # price, risk, performance
    symbol: Optional[str]
    portfolio_id: Optional[str]
    prediction_data: Dict[str, Any]
    confidence: float
    generated_at: datetime
    
    @property
    def event_type(self) -> str:
        return "MLPredictionGenerated"


# ============================================================================
# COMPLIANCE EVENTS (Australian Regulations)
# ============================================================================

@dataclass
class ConsentRecorded:
    """Notification consent recorded (Privacy Act compliance)"""
    event_id: str
    consent_id: str
    tenant_id: str
    client_id: str
    user_id: str
    notification_types: List[NotificationType]
    channels: List[DeliveryChannel]
    consent_given: bool
    consent_text: str
    ip_address: Optional[str]
    recorded_at: datetime
    
    @property
    def event_type(self) -> str:
        return "ConsentRecorded"


@dataclass
class ConsentWithdrawn:
    """Notification consent withdrawn"""
    event_id: str
    consent_id: str
    tenant_id: str
    client_id: str
    user_id: str
    notification_types: List[NotificationType]
    withdrawn_at: datetime
    
    @property
    def event_type(self) -> str:
        return "ConsentWithdrawn"


@dataclass
class NotificationAuditLogged:
    """Notification audit log (ASIC compliance)"""
    event_id: str
    audit_id: str
    tenant_id: str
    client_id: str
    notification_id: str
    notification_type: NotificationType
    action: str  # created, sent, delivered, read, failed
    channel: Optional[DeliveryChannel]
    status: DeliveryStatus
    metadata: Dict[str, Any]
    logged_at: datetime
    
    @property
    def event_type(self) -> str:
        return "NotificationAuditLogged"
