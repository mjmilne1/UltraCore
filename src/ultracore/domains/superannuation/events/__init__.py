"""Wealth Management Domain Events"""
from .base import WealthEvent
from .portfolio import (
    PortfolioCreatedEvent,
    PortfolioFundedEvent,
    TradeExecutedEvent,
    DividendReceivedEvent,
    RebalancedEvent
)
from .funds import (
    ManagedFundSubscribedEvent,
    ManagedFundRedeemedEvent,
    FundDistributionReceivedEvent
)
from .margin import (
    MarginLoanDrawnEvent,
    MarginCallIssuedEvent,
    MarginCallMetEvent
)

__all__ = [
    "WealthEvent",
    "PortfolioCreatedEvent",
    "PortfolioFundedEvent",
    "TradeExecutedEvent",
    "DividendReceivedEvent",
    "RebalancedEvent",
    "ManagedFundSubscribedEvent",
    "ManagedFundRedeemedEvent",
    "FundDistributionReceivedEvent",
    "MarginLoanDrawnEvent",
    "MarginCallIssuedEvent",
    "MarginCallMetEvent",
]
