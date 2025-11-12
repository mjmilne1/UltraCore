"""Base Event for Lending Domain"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

from ultracore.events.base import DomainEvent


class LendingEvent(DomainEvent):
    """
    Base class for all Lending domain events.
    
    Australian Lending Context:
    - NCCP (National Consumer Credit Protection Act)
    - Responsible lending obligations
    - Assessment of unsuitability
    - Credit reporting (Comprehensive Credit Reporting)
    - APRA prudential standards
    
    Integration Points:
    - Kafka: Event streaming and audit
    - UltraLedger: Loan accounting (double-entry)
    - Collateral: Security management (PPSR)
    - Restructuring: Hardship assistance (NCCP Section 72)
    - Accounts: Disbursement and repayments
    
    Kafka Topic: ultracore.lending.events
    Partition Key: loan_id
    """
    
    aggregate_type: str = "Loan"
    domain: str = "lending"
    
    kafka_topic: str = "ultracore.lending.events"
    kafka_partition_key: str = "loan_id"
    
    # Common fields
    loan_id: str
    customer_id: str
    loan_type: str  # personal, home, business, loc, bnpl
    
    # UltraLedger integration
    ledger_entry_id: Optional[str] = None
    
    # Regulatory
    nccp_regulated: bool = True  # Most consumer loans
    responsible_lending_assessed: bool = False
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
