"""
ETF Universe Manager
Manages ASX-listed ETF universe with business rules
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import List, Dict, Optional
import logging

from ..models import ETF, AssetClass, ETFCategory, BUSINESS_RULES

logger = logging.getLogger(__name__)


class ETFUniverseManager:
    """
    ETF Universe Manager for Investment Pods
    
    Maintains universe of ASX-listed ETFs with business rules:
    - AUM > $50M
    - Daily volume > $500K
    - Expense ratio < 1.0%
    - Min 12 months track record
    """
    
    def __init__(self):
        self.min_aum = BUSINESS_RULES["etf_selection"]["min_aum"]
        self.min_daily_volume = BUSINESS_RULES["etf_selection"]["min_daily_volume"]
        self.max_expense_ratio = BUSINESS_RULES["etf_selection"]["max_expense_ratio"]
        self.min_track_record_months = BUSINESS_RULES["etf_selection"]["min_track_record_months"]
        
        # Initialize ETF universe
        self.etf_universe = self._initialize_etf_universe()
    
    def _initialize_etf_universe(self) -> List[ETF]:
        """
        Initialize ETF universe with top ASX-listed ETFs
        
        In production, this would load from database with real-time data
        """
        etfs = [
            # Australian Shares - Large Cap
            ETF(
                etf_code="VAS",
                etf_name="Vanguard Australian Shares Index ETF",
                provider="Vanguard",
                asset_class=AssetClass.AUSTRALIAN_EQUITY,
                category=ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP,
                expense_ratio=Decimal("0.10"),
                aum=Decimal("12000000000"),  # $12B
                avg_daily_volume=Decimal("15000000"),  # $15M
                inception_date=date(2009, 5, 7),
                franking_yield=Decimal("3.5"),
                distribution_yield=Decimal("4.2"),
                returns_1y=Decimal("12.5"),
                returns_3y=Decimal("9.8"),
                returns_5y=Decimal("8.7"),
                volatility=Decimal("14.2"),
                sharpe_ratio=Decimal("0.62"),
                max_drawdown=Decimal("18.5")
            ),
            ETF(
                etf_code="IOZ",
                etf_name="iShares Core S&P/ASX 200 ETF",
                provider="iShares",
                asset_class=AssetClass.AUSTRALIAN_EQUITY,
                category=ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP,
                expense_ratio=Decimal("0.09"),
                aum=Decimal("8500000000"),  # $8.5B
                avg_daily_volume=Decimal("12000000"),
                inception_date=date(2010, 9, 24),
                franking_yield=Decimal("3.4"),
                distribution_yield=Decimal("4.0"),
                returns_1y=Decimal("12.3"),
                returns_3y=Decimal("9.6"),
                returns_5y=Decimal("8.5"),
                volatility=Decimal("14.0"),
                sharpe_ratio=Decimal("0.61"),
                max_drawdown=Decimal("18.2")
            ),
            ETF(
                etf_code="A200",
                etf_name="BetaShares Australia 200 ETF",
                provider="BetaShares",
                asset_class=AssetClass.AUSTRALIAN_EQUITY,
                category=ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP,
                expense_ratio=Decimal("0.07"),
                aum=Decimal("4200000000"),  # $4.2B
                avg_daily_volume=Decimal("8000000"),
                inception_date=date(2018, 5, 8),
                franking_yield=Decimal("3.3"),
                distribution_yield=Decimal("3.9"),
                returns_1y=Decimal("12.4"),
                returns_3y=Decimal("9.7"),
                returns_5y=Decimal("8.6"),
                volatility=Decimal("13.9"),
                sharpe_ratio=Decimal("0.63"),
                max_drawdown=Decimal("18.0")
            ),
            
            # Australian Shares - Small Cap
            ETF(
                etf_code="VSO",
                etf_name="Vanguard MSCI Australian Small Companies Index ETF",
                provider="Vanguard",
                asset_class=AssetClass.AUSTRALIAN_EQUITY,
                category=ETFCategory.AUSTRALIAN_SHARES_SMALL_CAP,
                expense_ratio=Decimal("0.30"),
                aum=Decimal("950000000"),  # $950M
                avg_daily_volume=Decimal("2500000"),
                inception_date=date(2011, 5, 12),
                franking_yield=Decimal("2.8"),
                distribution_yield=Decimal("3.5"),
                returns_1y=Decimal("15.2"),
                returns_3y=Decimal("11.5"),
                returns_5y=Decimal("10.2"),
                volatility=Decimal("18.5"),
                sharpe_ratio=Decimal("0.58"),
                max_drawdown=Decimal("24.5")
            ),
            
            # International Shares - Developed
            ETF(
                etf_code="VGS",
                etf_name="Vanguard MSCI Index International Shares ETF",
                provider="Vanguard",
                asset_class=AssetClass.INTERNATIONAL_EQUITY,
                category=ETFCategory.INTERNATIONAL_SHARES_DEVELOPED,
                expense_ratio=Decimal("0.18"),
                aum=Decimal("10500000000"),  # $10.5B
                avg_daily_volume=Decimal("18000000"),
                inception_date=date(2014, 11, 18),
                franking_yield=Decimal("0.0"),  # No franking for international
                distribution_yield=Decimal("1.8"),
                returns_1y=Decimal("18.5"),
                returns_3y=Decimal("14.2"),
                returns_5y=Decimal("12.8"),
                volatility=Decimal("16.5"),
                sharpe_ratio=Decimal("0.78"),
                max_drawdown=Decimal("20.5")
            ),
            ETF(
                etf_code="IVV",
                etf_name="iShares S&P 500 ETF",
                provider="iShares",
                asset_class=AssetClass.INTERNATIONAL_EQUITY,
                category=ETFCategory.INTERNATIONAL_SHARES_DEVELOPED,
                expense_ratio=Decimal("0.04"),
                aum=Decimal("7800000000"),  # $7.8B
                avg_daily_volume=Decimal("14000000"),
                inception_date=date(2010, 5, 5),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("1.5"),
                returns_1y=Decimal("20.2"),
                returns_3y=Decimal("15.8"),
                returns_5y=Decimal("14.2"),
                volatility=Decimal("17.2"),
                sharpe_ratio=Decimal("0.85"),
                max_drawdown=Decimal("21.5")
            ),
            ETF(
                etf_code="NDQ",
                etf_name="BetaShares NASDAQ 100 ETF",
                provider="BetaShares",
                asset_class=AssetClass.INTERNATIONAL_EQUITY,
                category=ETFCategory.INTERNATIONAL_SHARES_DEVELOPED,
                expense_ratio=Decimal("0.48"),
                aum=Decimal("5200000000"),  # $5.2B
                avg_daily_volume=Decimal("22000000"),
                inception_date=date(2015, 5, 20),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("0.8"),
                returns_1y=Decimal("28.5"),
                returns_3y=Decimal("22.5"),
                returns_5y=Decimal("20.2"),
                volatility=Decimal("22.5"),
                sharpe_ratio=Decimal("0.92"),
                max_drawdown=Decimal("28.5")
            ),
            
            # International Shares - Emerging Markets
            ETF(
                etf_code="VGE",
                etf_name="Vanguard FTSE Emerging Markets Shares ETF",
                provider="Vanguard",
                asset_class=AssetClass.INTERNATIONAL_EQUITY,
                category=ETFCategory.INTERNATIONAL_SHARES_EMERGING,
                expense_ratio=Decimal("0.48"),
                aum=Decimal("850000000"),  # $850M
                avg_daily_volume=Decimal("1800000"),
                inception_date=date(2013, 11, 19),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("2.5"),
                returns_1y=Decimal("8.5"),
                returns_3y=Decimal("6.2"),
                returns_5y=Decimal("5.8"),
                volatility=Decimal("20.5"),
                sharpe_ratio=Decimal("0.28"),
                max_drawdown=Decimal("26.5")
            ),
            
            # Australian Bonds
            ETF(
                etf_code="VAF",
                etf_name="Vanguard Australian Fixed Interest Index ETF",
                provider="Vanguard",
                asset_class=AssetClass.FIXED_INCOME,
                category=ETFCategory.AUSTRALIAN_BONDS,
                expense_ratio=Decimal("0.20"),
                aum=Decimal("2800000000"),  # $2.8B
                avg_daily_volume=Decimal("4500000"),
                inception_date=date(2012, 9, 27),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("3.8"),
                returns_1y=Decimal("4.2"),
                returns_3y=Decimal("2.8"),
                returns_5y=Decimal("2.5"),
                volatility=Decimal("4.5"),
                sharpe_ratio=Decimal("0.18"),
                max_drawdown=Decimal("6.5")
            ),
            ETF(
                etf_code="BOND",
                etf_name="BetaShares Australian Investment Grade Bond ETF",
                provider="BetaShares",
                asset_class=AssetClass.FIXED_INCOME,
                category=ETFCategory.AUSTRALIAN_BONDS,
                expense_ratio=Decimal("0.22"),
                aum=Decimal("1200000000"),  # $1.2B
                avg_daily_volume=Decimal("2500000"),
                inception_date=date(2017, 3, 8),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("4.0"),
                returns_1y=Decimal("4.5"),
                returns_3y=Decimal("3.0"),
                returns_5y=Decimal("2.7"),
                volatility=Decimal("4.2"),
                sharpe_ratio=Decimal("0.24"),
                max_drawdown=Decimal("6.0")
            ),
            
            # International Bonds
            ETF(
                etf_code="VGB",
                etf_name="Vanguard Australian Government Bond Index ETF",
                provider="Vanguard",
                asset_class=AssetClass.FIXED_INCOME,
                category=ETFCategory.INTERNATIONAL_BONDS,
                expense_ratio=Decimal("0.20"),
                aum=Decimal("1500000000"),  # $1.5B
                avg_daily_volume=Decimal("2000000"),
                inception_date=date(2012, 9, 27),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("3.5"),
                returns_1y=Decimal("3.8"),
                returns_3y=Decimal("2.5"),
                returns_5y=Decimal("2.2"),
                volatility=Decimal("4.8"),
                sharpe_ratio=Decimal("0.12"),
                max_drawdown=Decimal("7.0")
            ),
            
            # Cash Enhanced
            ETF(
                etf_code="BILL",
                etf_name="BetaShares Australian Bank Senior Floating Rate Bond ETF",
                provider="BetaShares",
                asset_class=AssetClass.CASH,
                category=ETFCategory.CASH_ENHANCED,
                expense_ratio=Decimal("0.22"),
                aum=Decimal("750000000"),  # $750M
                avg_daily_volume=Decimal("1500000"),
                inception_date=date(2016, 8, 17),
                franking_yield=Decimal("0.0"),
                distribution_yield=Decimal("4.5"),
                returns_1y=Decimal("4.8"),
                returns_3y=Decimal("3.5"),
                returns_5y=Decimal("3.2"),
                volatility=Decimal("2.5"),
                sharpe_ratio=Decimal("0.32"),
                max_drawdown=Decimal("3.5")
            ),
        ]
        
        # Apply business rules
        for etf in etfs:
            etf.meets_aum_threshold = etf.aum >= self.min_aum
            etf.meets_volume_threshold = etf.avg_daily_volume >= self.min_daily_volume
            etf.meets_expense_threshold = etf.expense_ratio <= self.max_expense_ratio
        
        logger.info(f"ETF universe initialized: {len(etfs)} ETFs")
        return etfs
    
    def get_eligible_etfs(self) -> List[ETF]:
        """Get all eligible ETFs meeting business rules"""
        eligible = [etf for etf in self.etf_universe if etf.is_eligible]
        logger.info(f"Eligible ETFs: {len(eligible)}/{len(self.etf_universe)}")
        return eligible
    
    def get_etfs_by_asset_class(self, asset_class: AssetClass) -> List[ETF]:
        """Get ETFs filtered by asset class"""
        return [etf for etf in self.etf_universe if etf.asset_class == asset_class and etf.is_eligible]
    
    def get_etfs_by_category(self, category: ETFCategory) -> List[ETF]:
        """Get ETFs filtered by category"""
        return [etf for etf in self.etf_universe if etf.category == category and etf.is_eligible]
    
    def get_etf_by_code(self, etf_code: str) -> Optional[ETF]:
        """Get specific ETF by code"""
        return next((etf for etf in self.etf_universe if etf.etf_code == etf_code), None)
    
    def get_top_etfs_by_sharpe(self, n: int = 10) -> List[ETF]:
        """Get top N ETFs by Sharpe ratio"""
        eligible = self.get_eligible_etfs()
        sorted_etfs = sorted(eligible, key=lambda e: e.sharpe_ratio or Decimal("0"), reverse=True)
        return sorted_etfs[:n]
    
    def get_top_etfs_by_franking(self, n: int = 5) -> List[ETF]:
        """Get top N ETFs by franking yield"""
        eligible = self.get_eligible_etfs()
        sorted_etfs = sorted(eligible, key=lambda e: e.franking_yield, reverse=True)
        return sorted_etfs[:n]
    
    def get_low_cost_etfs(self, max_expense: Optional[Decimal] = None) -> List[ETF]:
        """Get low-cost ETFs"""
        threshold = max_expense or Decimal("0.20")  # 0.20% default
        return [etf for etf in self.get_eligible_etfs() if etf.expense_ratio <= threshold]
    
    def calculate_universe_statistics(self) -> Dict:
        """Calculate statistics for ETF universe"""
        eligible = self.get_eligible_etfs()
        
        if not eligible:
            return {}
        
        total_aum = sum(etf.aum for etf in eligible)
        avg_expense_ratio = sum(etf.expense_ratio for etf in eligible) / len(eligible)
        avg_returns_3y = sum(etf.returns_3y or Decimal("0") for etf in eligible) / len(eligible)
        avg_volatility = sum(etf.volatility or Decimal("0") for etf in eligible) / len(eligible)
        
        # Count by asset class
        by_asset_class = {}
        for etf in eligible:
            asset_class = etf.asset_class.value
            by_asset_class[asset_class] = by_asset_class.get(asset_class, 0) + 1
        
        # Count by provider
        by_provider = {}
        for etf in eligible:
            provider = etf.provider
            by_provider[provider] = by_provider.get(provider, 0) + 1
        
        return {
            "total_etfs": len(eligible),
            "total_aum": total_aum,
            "avg_expense_ratio": avg_expense_ratio,
            "avg_returns_3y": avg_returns_3y,
            "avg_volatility": avg_volatility,
            "by_asset_class": by_asset_class,
            "by_provider": by_provider
        }
    
    def validate_portfolio_diversification(
        self,
        allocation: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Validate portfolio meets diversification rules
        
        Returns (is_valid, list_of_violations)
        """
        violations = []
        
        # Check max ETFs
        max_etfs = BUSINESS_RULES["portfolio_construction"]["max_etfs"]
        if len(allocation) > max_etfs:
            violations.append(f"Too many ETFs: {len(allocation)} > {max_etfs}")
        
        # Check individual weights
        min_weight = BUSINESS_RULES["portfolio_construction"]["min_etf_weight"]
        max_weight = BUSINESS_RULES["portfolio_construction"]["max_etf_weight"]
        
        for holding in allocation:
            weight = holding.get("weight", Decimal("0"))
            if weight < min_weight:
                violations.append(f"{holding['etf_code']}: weight {weight}% < minimum {min_weight}%")
            if weight > max_weight:
                violations.append(f"{holding['etf_code']}: weight {weight}% > maximum {max_weight}%")
        
        # Check single provider concentration
        max_single_provider = BUSINESS_RULES["portfolio_construction"]["max_single_provider"]
        provider_weights = {}
        
        for holding in allocation:
            etf = self.get_etf_by_code(holding["etf_code"])
            if etf:
                provider = etf.provider
                provider_weights[provider] = provider_weights.get(provider, Decimal("0")) + holding.get("weight", Decimal("0"))
        
        for provider, weight in provider_weights.items():
            if weight > max_single_provider:
                violations.append(f"Provider {provider}: {weight}% > maximum {max_single_provider}%")
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def refresh_etf_data(self, etf_code: str, updated_data: Dict) -> bool:
        """
        Refresh ETF data (for real-time updates)
        
        In production, this would fetch from market data provider
        """
        etf = self.get_etf_by_code(etf_code)
        if not etf:
            return False
        
        # Update fields
        if "returns_1y" in updated_data:
            etf.returns_1y = Decimal(str(updated_data["returns_1y"]))
        if "volatility" in updated_data:
            etf.volatility = Decimal(str(updated_data["volatility"]))
        if "sharpe_ratio" in updated_data:
            etf.sharpe_ratio = Decimal(str(updated_data["sharpe_ratio"]))
        
        logger.info(f"ETF data refreshed: {etf_code}")
        return True
