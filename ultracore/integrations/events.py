"""Integration Framework Events"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum

class IntegrationType(Enum):
    """Integration types"""
    ACCOUNTING = "accounting"
    TAX = "tax"
    BROKER = "broker"
    DATA_PROVIDER = "data_provider"
    WEBHOOK = "webhook"

class IntegrationProvider(Enum):
    """Integration providers"""
    # Australian Accounting
    XERO_AU = "xero_au"
    MYOB = "myob"
    QUICKBOOKS_AU = "quickbooks_au"
    
    # Australian Tax
    MYTAX_ATO = "mytax_ato"
    HR_BLOCK_AU = "hr_block_au"
    
    # Australian Brokers
    OPENMARKETS = "openmarkets"
    PHILLIPCAPITAL = "phillipcapital"
    COMMSEC = "commsec"
    NABTRADE = "nabtrade"
    
    # Data Providers
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    ASX_DATA = "asx_data"

class WebhookEvent(Enum):
    """Webhook event types"""
    PORTFOLIO_CREATED = "portfolio.created"
    PORTFOLIO_UPDATED = "portfolio.updated"
    TRADE_EXECUTED = "trade.executed"
    ORDER_PLACED = "order.placed"
    ORDER_FILLED = "order.filled"
    PRICE_ALERT_TRIGGERED = "price_alert.triggered"
    REBALANCING_COMPLETED = "rebalancing.completed"
    COMPLIANCE_BREACH = "compliance.breach"
    FEE_CHARGED = "fee.charged"

@dataclass
class IntegrationCreatedEvent:
    """Integration created"""
    integration_id: str
    integration_name: str
    integration_type: IntegrationType
    provider: IntegrationProvider
    user_id: str
    tenant_id: str
    configuration: Dict
    is_active: bool
    created_by: str
    timestamp: datetime

@dataclass
class IntegrationAuthenticatedEvent:
    """Integration authenticated"""
    integration_id: str
    provider: IntegrationProvider
    auth_method: str  # oauth2, api_key, etc.
    expires_at: Optional[datetime]
    timestamp: datetime

@dataclass
class IntegrationSyncStartedEvent:
    """Integration sync started"""
    sync_id: str
    integration_id: str
    sync_type: str  # full, incremental
    started_by: str
    timestamp: datetime

@dataclass
class IntegrationSyncCompletedEvent:
    """Integration sync completed"""
    sync_id: str
    integration_id: str
    records_synced: int
    records_failed: int
    duration_seconds: float
    timestamp: datetime

@dataclass
class IntegrationSyncFailedEvent:
    """Integration sync failed"""
    sync_id: str
    integration_id: str
    error_message: str
    error_code: Optional[str]
    timestamp: datetime

@dataclass
class WebhookRegisteredEvent:
    """Webhook registered"""
    webhook_id: str
    url: str
    events: List[WebhookEvent]
    secret: str
    is_active: bool
    user_id: str
    tenant_id: str
    created_by: str
    timestamp: datetime

@dataclass
class WebhookTriggeredEvent:
    """Webhook triggered"""
    webhook_id: str
    event_type: WebhookEvent
    payload: Dict
    timestamp: datetime

@dataclass
class WebhookDeliveredEvent:
    """Webhook delivered successfully"""
    webhook_id: str
    delivery_id: str
    event_type: WebhookEvent
    status_code: int
    response_time_ms: float
    timestamp: datetime

@dataclass
class WebhookFailedEvent:
    """Webhook delivery failed"""
    webhook_id: str
    delivery_id: str
    event_type: WebhookEvent
    error_message: str
    status_code: Optional[int]
    retry_count: int
    timestamp: datetime

@dataclass
class AccountingDataExportedEvent:
    """Data exported to accounting system"""
    export_id: str
    integration_id: str
    provider: IntegrationProvider
    export_type: str  # transactions, invoices, etc.
    record_count: int
    date_range_start: datetime
    date_range_end: datetime
    timestamp: datetime

@dataclass
class TaxDataExportedEvent:
    """Data exported to tax system"""
    export_id: str
    integration_id: str
    provider: IntegrationProvider
    tax_year: str
    capital_gains_count: int
    dividend_count: int
    interest_count: int
    timestamp: datetime

@dataclass
class BrokerOrderSyncedEvent:
    """Order synced with broker"""
    sync_id: str
    integration_id: str
    order_id: str
    broker_order_id: str
    status: str
    timestamp: datetime

@dataclass
class IntegrationDisabledEvent:
    """Integration disabled"""
    integration_id: str
    reason: str
    disabled_by: str
    timestamp: datetime

@dataclass
class IntegrationDeletedEvent:
    """Integration deleted"""
    integration_id: str
    deleted_by: str
    timestamp: datetime
