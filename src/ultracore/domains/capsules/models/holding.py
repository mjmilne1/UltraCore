"""Holding Model - Individual Asset"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from .enums import AssetClass


class Holding(BaseModel):
    """
    Holding - Individual Asset.
    
    From TuringMachines: 2,428 holdings
    
    Represents a single tradeable asset that can be
    included in capsules.
    
    Examples:
    - CBA.AX (Commonwealth Bank)
    - AAPL (Apple Inc.)
    - BTC-USD (Bitcoin)
    - VAS.AX (Vanguard Australian Shares ETF)
    """
    
    # Identity
    holding_id: str
    ticker: str  # Trading symbol
    name: str
    
    # Classification
    asset_class: AssetClass
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Geography
    country: str
    exchange: str
    currency: str
    
    # Market data
    current_price: Decimal
    market_cap: Optional[Decimal] = None
    
    # Fundamental
    pe_ratio: Optional[Decimal] = None
    dividend_yield: Optional[Decimal] = None
    
    # ESG
    esg_score: Optional[Decimal] = None
    
    # Trading
    tradeable: bool = True
    fractional_shares_supported: bool = False
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }
