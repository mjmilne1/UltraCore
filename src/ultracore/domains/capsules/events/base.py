"""Base Event for Capsules Domain"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel

from ultracore.events.base import DomainEvent


class CapsuleEvent(DomainEvent):
    """
    Base class for all Capsules events.
    
    Capsules Business Context:
    ==========================
    
    From TuringMachines:
    - 500 pre-built portfolios (capsules)
    - 2,428 holdings (tradeable assets)
    - Goal-based investing approach
    - Automatic rebalancing
    - Data mesh architecture
    
    Capsule Types:
    ==============
    
    1. Dividend Growth
       - Focus: High dividend yield
       - Example: Aussie Dividend Champion
       - Risk: Medium
       - Return: 8-10% p.a.
    
    2. Tech Growth
       - Focus: Technology sector
       - Example: Tech Titans (FAANG)
       - Risk: High
       - Return: 15-20% p.a.
    
    3. ESG/Sustainable
       - Focus: Environmental/social impact
       - Example: ESG Future
       - Risk: Medium-High
       - Return: 12-15% p.a.
    
    4. Real Estate
       - Focus: Property exposure via REITs
       - Example: Property Exposure
       - Risk: Medium
       - Return: 8-12% p.a.
    
    5. Global Diversified
       - Focus: Worldwide allocation
       - Example: Global Diversifier
       - Risk: Medium
       - Return: 10-12% p.a.
    
    6. Cryptocurrency
       - Focus: Crypto via futures
       - Example: Bitcoin Futures
       - Risk: Very High
       - Return: Highly volatile
    
    Revenue Model:
    ==============
    
    Management Fee: 0.60% p.a. of AUM
    
    Example:
    - 10,000 customers
    - Average investment: $50,000
    - Total AUM: $500M
    - Annual revenue: $3M
    
    At scale (100,000 customers):
    - Total AUM: $5B
    - Annual revenue: $30M ??
    
    Rebalancing:
    ============
    
    Automatic rebalancing when holdings drift from targets:
    - Daily: High-volatility capsules
    - Weekly: Momentum strategies
    - Monthly: Standard capsules
    - Quarterly: Conservative capsules
    
    Kafka Topic: ultracore.capsules.events
    Partition Key: capsule_id
    """
    
    aggregate_type: str = "Capsule"
    domain: str = "capsules"
    
    kafka_topic: str = "ultracore.capsules.events"
    kafka_partition_key: str = "capsule_id"
    
    # Common fields
    capsule_id: Optional[str] = None
    customer_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
