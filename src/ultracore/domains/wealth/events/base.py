"""Base Event for Wealth Domain"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

from ultracore.events.base import DomainEvent


class WealthEvent(DomainEvent):
    """
    Base class for all Wealth domain events.
    
    Australian Investment Context:
    - ASX (Australian Securities Exchange)
    - ASIC (Australian Securities and Investments Commission)
    - APRA (Australian Prudential Regulation Authority)
    - CHESS (Clearing House Electronic Subregister System)
    - HIN (Holder Identification Number)
    - SRN (Securityholder Reference Number)
    
    Integration Points:
    - Kafka: Event streaming and audit
    - UltraLedger: Investment accounting (double-entry)
    - UltraOptimiser: Portfolio optimization (existing)
    - Accounts: Cash management and settlements
    - Lending: Margin lending integration
    
    Kafka Topic: ultracore.wealth.events
    Partition Key: portfolio_id
    """
    
    aggregate_type: str = "Portfolio"
    domain: str = "wealth"
    
    kafka_topic: str = "ultracore.wealth.events"
    kafka_partition_key: str = "portfolio_id"
    
    # Common fields
    portfolio_id: str
    customer_id: str
    
    # UltraLedger integration
    ledger_entry_id: Optional[str] = None
    
    # Regulatory
    asic_regulated: bool = True
    chess_settlement: bool = False
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
