"""
Notification Aggregates
Event-sourced aggregates for notification system
"""

from .alert import (
    PriceAlertAggregate,
    PortfolioAlertAggregate,
    NewsAlertAggregate
)

from .notification import (
    NotificationAggregate,
    NotificationPreferenceAggregate,
    ConsentAggregate
)

__all__ = [
    "PriceAlertAggregate",
    "PortfolioAlertAggregate",
    "NewsAlertAggregate",
    "NotificationAggregate",
    "NotificationPreferenceAggregate",
    "ConsentAggregate"
]
