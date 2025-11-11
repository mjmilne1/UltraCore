"""
UltraCore Multi-Currency System - Currency Manager

Comprehensive currency and exchange rate management:
- ISO 4217 currency support
- Real-time exchange rate feeds
- Historical rate tracking
- Rate sources (Central banks, market data)
- AI-powered rate forecasting
- Currency pair management
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
import asyncio
import aiohttp


# ============================================================================
# Currency Enums
# ============================================================================

class CurrencyCode(str, Enum):
    """ISO 4217 Currency Codes"""
    # Major currencies
    AUD = "AUD"  # Australian Dollar
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    JPY = "JPY"  # Japanese Yen
    CHF = "CHF"  # Swiss Franc
    CAD = "CAD"  # Canadian Dollar
    
    # Asia-Pacific
    NZD = "NZD"  # New Zealand Dollar
    SGD = "SGD"  # Singapore Dollar
    HKD = "HKD"  # Hong Kong Dollar
    CNY = "CNY"  # Chinese Yuan
    INR = "INR"  # Indian Rupee
    THB = "THB"  # Thai Baht
    MYR = "MYR"  # Malaysian Ringgit
    IDR = "IDR"  # Indonesian Rupiah
    PHP = "PHP"  # Philippine Peso
    VND = "VND"  # Vietnamese Dong
    
    # Crypto (future support)
    BTC = "BTC"  # Bitcoin
    ETH = "ETH"  # Ethereum
    USDT = "USDT"  # Tether


class RateSource(str, Enum):
    """Exchange rate data sources"""
    RBA = "RBA"  # Reserve Bank of Australia
    ECB = "ECB"  # European Central Bank
    FED = "FED"  # Federal Reserve
    MARKET = "MARKET"  # Market rates (Bloomberg, Reuters)
    MANUAL = "MANUAL"  # Manually entered
    AI_FORECAST = "AI_FORECAST"  # AI-predicted rates


class RateType(str, Enum):
    """Type of exchange rate"""
    SPOT = "SPOT"  # Current market rate
    BUY = "BUY"  # Bank buying rate
    SELL = "SELL"  # Bank selling rate
    MID = "MID"  # Mid-market rate
    FORWARD = "FORWARD"  # Forward rate
    HISTORICAL = "HISTORICAL"  # Historical rate


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Currency:
    """Currency definition"""
    code: CurrencyCode
    name: str
    symbol: str
    numeric_code: str  # ISO 4217 numeric
    
    # Decimal properties
    minor_units: int = 2  # Number of decimal places
    
    # Display
    symbol_position: str = "before"  # "before" or "after"
    thousands_separator: str = ","
    decimal_separator: str = "."
    
    # Status
    active: bool = True
    
    # Country/region
    countries: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExchangeRate:
    """Exchange rate between two currencies"""
    rate_id: str
    
    # Currency pair
    from_currency: CurrencyCode
    to_currency: CurrencyCode
    
    # Rate details
    rate: Decimal  # Exchange rate (from -> to)
    inverse_rate: Decimal  # Exchange rate (to -> from)
    
    # Rate metadata
    rate_type: RateType
    rate_source: RateSource
    effective_date: date
    effective_time: datetime
    
    # Spread (for buy/sell)
    spread_bps: Optional[int] = None  # Basis points
    
    # Validity
    valid_from: datetime = field(default_factory=datetime.utcnow)
    valid_to: Optional[datetime] = None
    
    # AI/ML
    ai_confidence: float = 1.0
    is_forecast: bool = False
    
    # Audit
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    def get_rate(self, from_curr: CurrencyCode, to_curr: CurrencyCode) -> Decimal:
        """Get rate for specific direction"""
        if from_curr == self.from_currency and to_curr == self.to_currency:
            return self.rate
        elif from_curr == self.to_currency and to_curr == self.from_currency:
            return self.inverse_rate
        else:
            raise ValueError(f"Rate not available for {from_curr}/{to_curr}")


@dataclass
class CurrencyPair:
    """Trading pair definition"""
    pair_id: str
    base_currency: CurrencyCode
    quote_currency: CurrencyCode
    
    # Trading properties
    min_trade_amount: Decimal
    max_trade_amount: Decimal
    pip_size: Decimal  # Smallest price increment
    
    # Spreads
    typical_spread_bps: int  # Basis points
    
    # Status
    active: bool = True
    trading_enabled: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_pair_name(self) -> str:
        """Get standard pair name (e.g., AUD/USD)"""
        return f"{self.base_currency.value}/{self.quote_currency.value}"


@dataclass
class RateHistory:
    """Historical exchange rate data"""
    currency_pair: str
    date: date
    open_rate: Decimal
    high_rate: Decimal
    low_rate: Decimal
    close_rate: Decimal
    
    # Volume (if available)
    volume: Optional[Decimal] = None
    
    # Source
    source: RateSource = RateSource.MARKET
    
    created_at: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# Currency Manager
# ============================================================================

class CurrencyManager:
    """
    Manages currencies and exchange rates
    Supports multiple rate sources and real-time updates
    """
    
    def __init__(self):
        self.currencies: Dict[CurrencyCode, Currency] = {}
        self.exchange_rates: Dict[str, ExchangeRate] = {}
        self.rate_history: List[RateHistory] = []
        self.currency_pairs: Dict[str, CurrencyPair] = {}
        
        # Initialize standard currencies
        self._initialize_currencies()
        self._initialize_currency_pairs()
    
    def _initialize_currencies(self):
        """Initialize standard currency definitions"""
        
        standard_currencies = [
            Currency(
                code=CurrencyCode.AUD,
                name="Australian Dollar",
                symbol="$",
                numeric_code="036",
                minor_units=2,
                symbol_position="before",
                countries=["Australia"]
            ),
            Currency(
                code=CurrencyCode.USD,
                name="United States Dollar",
                symbol="$",
                numeric_code="840",
                minor_units=2,
                symbol_position="before",
                countries=["United States"]
            ),
            Currency(
                code=CurrencyCode.EUR,
                name="Euro",
                symbol="€",
                numeric_code="978",
                minor_units=2,
                symbol_position="before",
                countries=["Eurozone"]
            ),
            Currency(
                code=CurrencyCode.GBP,
                name="British Pound Sterling",
                symbol="£",
                numeric_code="826",
                minor_units=2,
                symbol_position="before",
                countries=["United Kingdom"]
            ),
            Currency(
                code=CurrencyCode.JPY,
                name="Japanese Yen",
                symbol="¥",
                numeric_code="392",
                minor_units=0,  # Yen has no minor units
                symbol_position="before",
                countries=["Japan"]
            ),
            Currency(
                code=CurrencyCode.CHF,
                name="Swiss Franc",
                symbol="Fr",
                numeric_code="756",
                minor_units=2,
                symbol_position="before",
                countries=["Switzerland"]
            ),
            Currency(
                code=CurrencyCode.CAD,
                name="Canadian Dollar",
                symbol="$",
                numeric_code="124",
                minor_units=2,
                symbol_position="before",
                countries=["Canada"]
            ),
            Currency(
                code=CurrencyCode.NZD,
                name="New Zealand Dollar",
                symbol="$",
                numeric_code="554",
                minor_units=2,
                symbol_position="before",
                countries=["New Zealand"]
            ),
            Currency(
                code=CurrencyCode.SGD,
                name="Singapore Dollar",
                symbol="$",
                numeric_code="702",
                minor_units=2,
                symbol_position="before",
                countries=["Singapore"]
            ),
            Currency(
                code=CurrencyCode.CNY,
                name="Chinese Yuan",
                symbol="¥",
                numeric_code="156",
                minor_units=2,
                symbol_position="before",
                countries=["China"]
            ),
        ]
        
        for currency in standard_currencies:
            self.currencies[currency.code] = currency
    
    def _initialize_currency_pairs(self):
        """Initialize standard trading pairs"""
        
        standard_pairs = [
            # Major AUD pairs
            CurrencyPair(
                pair_id="AUDUSD",
                base_currency=CurrencyCode.AUD,
                quote_currency=CurrencyCode.USD,
                min_trade_amount=Decimal('1000'),
                max_trade_amount=Decimal('10000000'),
                pip_size=Decimal('0.0001'),
                typical_spread_bps=20
            ),
            CurrencyPair(
                pair_id="AUDEUR",
                base_currency=CurrencyCode.AUD,
                quote_currency=CurrencyCode.EUR,
                min_trade_amount=Decimal('1000'),
                max_trade_amount=Decimal('10000000'),
                pip_size=Decimal('0.0001'),
                typical_spread_bps=25
            ),
            CurrencyPair(
                pair_id="AUDGBP",
                base_currency=CurrencyCode.AUD,
                quote_currency=CurrencyCode.GBP,
                min_trade_amount=Decimal('1000'),
                max_trade_amount=Decimal('10000000'),
                pip_size=Decimal('0.0001'),
                typical_spread_bps=25
            ),
            CurrencyPair(
                pair_id="AUDJPY",
                base_currency=CurrencyCode.AUD,
                quote_currency=CurrencyCode.JPY,
                min_trade_amount=Decimal('1000'),
                max_trade_amount=Decimal('10000000'),
                pip_size=Decimal('0.01'),
                typical_spread_bps=20
            ),
            # USD pairs
            CurrencyPair(
                pair_id="EURUSD",
                base_currency=CurrencyCode.EUR,
                quote_currency=CurrencyCode.USD,
                min_trade_amount=Decimal('1000'),
                max_trade_amount=Decimal('10000000'),
                pip_size=Decimal('0.0001'),
                typical_spread_bps=10
            ),
            CurrencyPair(
                pair_id="GBPUSD",
                base_currency=CurrencyCode.GBP,
                quote_currency=CurrencyCode.USD,
                min_trade_amount=Decimal('1000'),
                max_trade_amount=Decimal('10000000'),
                pip_size=Decimal('0.0001'),
                typical_spread_bps=15
            ),
        ]
        
        for pair in standard_pairs:
            self.currency_pairs[pair.pair_id] = pair
    
    # ========================================================================
    # Currency Operations
    # ========================================================================
    
    def get_currency(self, code: CurrencyCode) -> Optional[Currency]:
        """Get currency by code"""
        return self.currencies.get(code)
    
    def list_currencies(self, active_only: bool = True) -> List[Currency]:
        """List all currencies"""
        currencies = list(self.currencies.values())
        if active_only:
            currencies = [c for c in currencies if c.active]
        return currencies
    
    def format_amount(
        self,
        amount: Decimal,
        currency: CurrencyCode
    ) -> str:
        """Format amount with currency symbol"""
        
        curr = self.get_currency(currency)
        if not curr:
            return f"{amount} {currency.value}"
        
        # Round to currency's minor units
        rounded = round(amount, curr.minor_units)
        
        # Format with separators
        amount_str = f"{rounded:,.{curr.minor_units}f}"
        amount_str = amount_str.replace(',', curr.thousands_separator)
        
        # Add symbol
        if curr.symbol_position == "before":
            return f"{curr.symbol}{amount_str}"
        else:
            return f"{amount_str}{curr.symbol}"
    
    # ========================================================================
    # Exchange Rate Operations
    # ========================================================================
    
    async def get_exchange_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate_type: RateType = RateType.MID,
        as_of: Optional[datetime] = None
    ) -> Optional[ExchangeRate]:
        """Get exchange rate between two currencies"""
        
        # Same currency
        if from_currency == to_currency:
            return ExchangeRate(
                rate_id=f"SAME-{from_currency.value}",
                from_currency=from_currency,
                to_currency=to_currency,
                rate=Decimal('1.0'),
                inverse_rate=Decimal('1.0'),
                rate_type=rate_type,
                rate_source=RateSource.MANUAL,
                effective_date=date.today(),
                effective_time=datetime.utcnow()
            )
        
        as_of_dt = as_of or datetime.utcnow()
        
        # Look for existing rate
        rate_key = f"{from_currency.value}/{to_currency.value}/{rate_type.value}"
        
        if rate_key in self.exchange_rates:
            rate = self.exchange_rates[rate_key]
            # Check if rate is still valid
            if rate.valid_to is None or rate.valid_to > as_of_dt:
                return rate
        
        # Try to fetch from external source
        rate = await self._fetch_rate_from_source(
            from_currency,
            to_currency,
            rate_type,
            as_of_dt
        )
        
        return rate
    
    async def _fetch_rate_from_source(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate_type: RateType,
        as_of: datetime
    ) -> Optional[ExchangeRate]:
        """Fetch rate from external source"""
        
        # In production, would integrate with:
        # - Reserve Bank of Australia API
        # - European Central Bank API
        # - Bloomberg/Reuters feeds
        # - Other market data providers
        
        # For now, return sample rates (AUD-centric)
        sample_rates = {
            (CurrencyCode.AUD, CurrencyCode.USD): Decimal('0.6500'),
            (CurrencyCode.AUD, CurrencyCode.EUR): Decimal('0.6000'),
            (CurrencyCode.AUD, CurrencyCode.GBP): Decimal('0.5200'),
            (CurrencyCode.AUD, CurrencyCode.JPY): Decimal('95.00'),
            (CurrencyCode.AUD, CurrencyCode.NZD): Decimal('1.0800'),
            (CurrencyCode.AUD, CurrencyCode.SGD): Decimal('0.8700'),
            (CurrencyCode.AUD, CurrencyCode.CNY): Decimal('4.6500'),
            (CurrencyCode.USD, CurrencyCode.EUR): Decimal('0.9200'),
            (CurrencyCode.EUR, CurrencyCode.USD): Decimal('1.0870'),
            (CurrencyCode.GBP, CurrencyCode.USD): Decimal('1.2500'),
        }
        
        # Try direct pair
        pair = (from_currency, to_currency)
        if pair in sample_rates:
            rate = sample_rates[pair]
        else:
            # Try inverse
            inverse_pair = (to_currency, from_currency)
            if inverse_pair in sample_rates:
                rate = Decimal('1.0') / sample_rates[inverse_pair]
            else:
                # Cross rate via USD
                if from_currency != CurrencyCode.USD and to_currency != CurrencyCode.USD:
                    from_usd = sample_rates.get((from_currency, CurrencyCode.USD))
                    to_usd = sample_rates.get((to_currency, CurrencyCode.USD))
                    if from_usd and to_usd:
                        rate = from_usd / to_usd
                    else:
                        return None
                else:
                    return None
        
        # Create rate object
        rate_id = f"RATE-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        exchange_rate = ExchangeRate(
            rate_id=rate_id,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            inverse_rate=Decimal('1.0') / rate,
            rate_type=rate_type,
            rate_source=RateSource.MARKET,
            effective_date=as_of.date(),
            effective_time=as_of
        )
        
        # Cache it
        rate_key = f"{from_currency.value}/{to_currency.value}/{rate_type.value}"
        self.exchange_rates[rate_key] = exchange_rate
        
        return exchange_rate
    
    async def convert_amount(
        self,
        amount: Decimal,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate_type: RateType = RateType.MID,
        as_of: Optional[datetime] = None
    ) -> Tuple[Decimal, ExchangeRate]:
        """
        Convert amount from one currency to another
        Returns: (converted_amount, exchange_rate_used)
        """
        
        rate = await self.get_exchange_rate(
            from_currency,
            to_currency,
            rate_type,
            as_of
        )
        
        if not rate:
            raise ValueError(
                f"No exchange rate available for {from_currency.value}/{to_currency.value}"
            )
        
        converted = amount * rate.rate
        
        # Round to target currency's minor units
        to_curr = self.get_currency(to_currency)
        if to_curr:
            converted = round(converted, to_curr.minor_units)
        
        return converted, rate
    
    async def set_exchange_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        rate: Decimal,
        rate_type: RateType = RateType.MID,
        rate_source: RateSource = RateSource.MANUAL,
        effective_date: Optional[date] = None,
        created_by: Optional[str] = None
    ) -> ExchangeRate:
        """Manually set an exchange rate"""
        
        rate_id = f"RATE-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        eff_date = effective_date or date.today()
        
        exchange_rate = ExchangeRate(
            rate_id=rate_id,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            inverse_rate=Decimal('1.0') / rate,
            rate_type=rate_type,
            rate_source=rate_source,
            effective_date=eff_date,
            effective_time=datetime.utcnow(),
            created_by=created_by
        )
        
        # Store it
        rate_key = f"{from_currency.value}/{to_currency.value}/{rate_type.value}"
        self.exchange_rates[rate_key] = exchange_rate
        
        return exchange_rate
    
    # ========================================================================
    # Historical Rates
    # ========================================================================
    
    async def get_historical_rate(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        as_of_date: date
    ) -> Optional[ExchangeRate]:
        """Get historical exchange rate for a specific date"""
        
        # Look in history
        pair_name = f"{from_currency.value}/{to_currency.value}"
        
        for history in self.rate_history:
            if history.currency_pair == pair_name and history.date == as_of_date:
                # Create rate object from historical data
                rate_id = f"HIST-{as_of_date.isoformat()}-{pair_name}"
                return ExchangeRate(
                    rate_id=rate_id,
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=history.close_rate,
                    inverse_rate=Decimal('1.0') / history.close_rate,
                    rate_type=RateType.HISTORICAL,
                    rate_source=RateSource.MARKET,
                    effective_date=as_of_date,
                    effective_time=datetime.combine(as_of_date, datetime.min.time())
                )
        
        # If not in cache, try to fetch
        return await self._fetch_rate_from_source(
            from_currency,
            to_currency,
            RateType.HISTORICAL,
            datetime.combine(as_of_date, datetime.min.time())
        )
    
    async def add_rate_history(
        self,
        currency_pair: str,
        date: date,
        open_rate: Decimal,
        high_rate: Decimal,
        low_rate: Decimal,
        close_rate: Decimal,
        source: RateSource = RateSource.MARKET
    ) -> RateHistory:
        """Add historical rate data"""
        
        history = RateHistory(
            currency_pair=currency_pair,
            date=date,
            open_rate=open_rate,
            high_rate=high_rate,
            low_rate=low_rate,
            close_rate=close_rate,
            source=source
        )
        
        self.rate_history.append(history)
        return history
    
    async def get_rate_trend(
        self,
        from_currency: CurrencyCode,
        to_currency: CurrencyCode,
        days: int = 30
    ) -> List[RateHistory]:
        """Get historical rate trend"""
        
        pair_name = f"{from_currency.value}/{to_currency.value}"
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        trend = [
            h for h in self.rate_history
            if h.currency_pair == pair_name and start_date <= h.date <= end_date
        ]
        
        return sorted(trend, key=lambda x: x.date)
    
    # ========================================================================
    # Currency Pair Operations
    # ========================================================================
    
    def get_currency_pair(self, pair_id: str) -> Optional[CurrencyPair]:
        """Get currency pair by ID"""
        return self.currency_pairs.get(pair_id)
    
    def list_currency_pairs(
        self,
        base_currency: Optional[CurrencyCode] = None,
        active_only: bool = True
    ) -> List[CurrencyPair]:
        """List currency pairs"""
        
        pairs = list(self.currency_pairs.values())
        
        if base_currency:
            pairs = [p for p in pairs if p.base_currency == base_currency]
        
        if active_only:
            pairs = [p for p in pairs if p.active]
        
        return pairs


# ============================================================================
# Global Currency Manager
# ============================================================================

_currency_manager: Optional[CurrencyManager] = None

def get_currency_manager() -> CurrencyManager:
    """Get the singleton currency manager"""
    global _currency_manager
    if _currency_manager is None:
        _currency_manager = CurrencyManager()
    return _currency_manager
