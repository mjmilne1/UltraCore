"""
Market Data Service
Yahoo Finance integration for Australian ETF data
"""

import sys
sys.path.append('/opt/.manus/.sandbox-runtime')

from decimal import Decimal
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import numpy as np

from data_api import ApiClient
from ..models import ETF, AssetClass, ETFCategory

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Market data service using Yahoo Finance API
    
    Fetches real-time and historical data for Australian ETFs
    """
    
    def __init__(self):
        self.api_client = ApiClient()
        self.region = "AU"
        self.lang = "en-AU"
        
        # Australian ETF universe (ASX codes)
        self.australian_etf_codes = [
            # Australian Equity - Large Cap
            "VAS.AX", "IOZ.AX", "A200.AX", "STW.AX", "VHY.AX",
            
            # Australian Equity - Small Cap
            "VSO.AX", "SMLL.AX",
            
            # International Equity - Developed
            "VGS.AX", "IVV.AX", "VTS.AX", "IWLD.AX", "NDQ.AX",
            "HNDQ.AX", "FANG.AX", "TECH.AX",
            
            # International Equity - Emerging
            "VGE.AX", "IEM.AX",
            
            # Australian Bonds
            "VAF.AX", "VGB.AX", "BOND.AX", "PLUS.AX",
            
            # International Bonds
            "VIF.AX", "IHCB.AX",
            
            # Property
            "VAP.AX", "DJRE.AX",
            
            # Cash/Enhanced Cash
            "BILL.AX", "AAA.AX",
            
            # Commodities
            "QAU.AX", "GOLD.AX",
        ]
    
    def fetch_etf_profile(self, etf_code: str) -> Optional[Dict]:
        """Fetch ETF profile from Yahoo Finance"""
        try:
            response = self.api_client.call_api(
                'YahooFinance/get_stock_profile',
                query={
                    'symbol': etf_code,
                    'region': self.region,
                    'lang': self.lang
                }
            )
            
            if not response:
                logger.warning(f"No profile data for {etf_code}")
                return None
            
            # Extract relevant data
            asset_profile = response.get('assetProfile', {})
            price = response.get('price', {})
            summary_detail = response.get('summaryDetail', {})
            
            profile = {
                'etf_code': etf_code.replace('.AX', ''),
                'etf_name': price.get('longName', ''),
                'provider': self._extract_provider(price.get('longName', '')),
                'expense_ratio': self._extract_decimal(summary_detail.get('totalAssets', {})),
                'aum': self._extract_decimal(summary_detail.get('totalAssets', {})),
                'currency': price.get('currency', 'AUD'),
            }
            
            logger.info(f"Fetched profile for {etf_code}")
            return profile
            
        except Exception as e:
            logger.error(f"Error fetching profile for {etf_code}: {e}")
            return None
    
    def fetch_etf_historical_data(
        self,
        etf_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Optional[Dict]:
        """
        Fetch historical price data for ETF
        
        Returns daily OHLCV data
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=5*365)  # 5 years
        if end_date is None:
            end_date = date.today()
        
        try:
            # Calculate range
            days_diff = (end_date - start_date).days
            if days_diff <= 7:
                range_param = "5d"
            elif days_diff <= 30:
                range_param = "1mo"
            elif days_diff <= 90:
                range_param = "3mo"
            elif days_diff <= 180:
                range_param = "6mo"
            elif days_diff <= 365:
                range_param = "1y"
            elif days_diff <= 730:
                range_param = "2y"
            elif days_diff <= 1825:
                range_param = "5y"
            else:
                range_param = "10y"
            
            response = self.api_client.call_api(
                'YahooFinance/get_stock_chart',
                query={
                    'symbol': etf_code,
                    'region': self.region,
                    'interval': '1d',
                    'range': range_param,
                    'includeAdjustedClose': True
                }
            )
            
            if not response or 'chart' not in response:
                logger.warning(f"No chart data for {etf_code}")
                return None
            
            chart = response['chart']
            if 'result' not in chart or not chart['result']:
                logger.warning(f"No result in chart for {etf_code}")
                return None
            
            result = chart['result'][0]
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            quote = indicators.get('quote', [{}])[0]
            adjclose = indicators.get('adjclose', [{}])[0]
            
            # Extract prices
            dates = [datetime.fromtimestamp(ts).date() for ts in timestamps]
            closes = quote.get('close', [])
            adj_closes = adjclose.get('adjclose', closes)
            volumes = quote.get('volume', [])
            
            historical_data = {
                'etf_code': etf_code.replace('.AX', ''),
                'dates': dates,
                'closes': closes,
                'adj_closes': adj_closes,
                'volumes': volumes,
                'start_date': dates[0] if dates else None,
                'end_date': dates[-1] if dates else None,
                'data_points': len(dates)
            }
            
            logger.info(f"Fetched {len(dates)} days of data for {etf_code}")
            return historical_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {etf_code}: {e}")
            return None
    
    def calculate_returns(
        self,
        historical_data: Dict,
        periods: List[int] = [252, 756, 1260]  # 1y, 3y, 5y in trading days
    ) -> Dict[str, Decimal]:
        """
        Calculate returns for different periods
        
        periods: list of trading days (252 = 1 year)
        """
        adj_closes = historical_data.get('adj_closes', [])
        
        if not adj_closes or len(adj_closes) < 2:
            return {}
        
        # Clean data (remove None values)
        adj_closes = [p for p in adj_closes if p is not None]
        
        if not adj_closes:
            return {}
        
        returns = {}
        current_price = adj_closes[-1]
        
        for period in periods:
            if len(adj_closes) > period:
                past_price = adj_closes[-period-1]
                if past_price and past_price > 0:
                    period_return = ((current_price - past_price) / past_price) * 100
                    
                    # Annualize
                    years = period / 252
                    annualized_return = (((current_price / past_price) ** (1 / years)) - 1) * 100
                    
                    if period == 252:
                        returns['returns_1y'] = Decimal(str(round(annualized_return, 2)))
                    elif period == 756:
                        returns['returns_3y'] = Decimal(str(round(annualized_return, 2)))
                    elif period == 1260:
                        returns['returns_5y'] = Decimal(str(round(annualized_return, 2)))
        
        return returns
    
    def calculate_volatility(self, historical_data: Dict) -> Decimal:
        """Calculate annualized volatility"""
        adj_closes = historical_data.get('adj_closes', [])
        
        if not adj_closes or len(adj_closes) < 2:
            return Decimal("15.0")  # Default
        
        # Clean data
        adj_closes = [p for p in adj_closes if p is not None]
        
        if len(adj_closes) < 2:
            return Decimal("15.0")
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(adj_closes)):
            if adj_closes[i-1] and adj_closes[i-1] > 0:
                ret = (adj_closes[i] - adj_closes[i-1]) / adj_closes[i-1]
                daily_returns.append(ret)
        
        if not daily_returns:
            return Decimal("15.0")
        
        # Annualized volatility
        volatility = np.std(daily_returns) * np.sqrt(252) * 100
        
        return Decimal(str(round(volatility, 2)))
    
    def calculate_sharpe_ratio(
        self,
        returns: Dict[str, Decimal],
        volatility: Decimal,
        risk_free_rate: Decimal = Decimal("4.0")
    ) -> Decimal:
        """Calculate Sharpe ratio"""
        # Use 3-year return if available
        annual_return = returns.get('returns_3y', returns.get('returns_1y', Decimal("8.0")))
        
        if volatility == 0:
            return Decimal("0")
        
        sharpe = (annual_return - risk_free_rate) / volatility
        return Decimal(str(round(sharpe, 3)))
    
    def calculate_max_drawdown(self, historical_data: Dict) -> Decimal:
        """Calculate maximum drawdown"""
        adj_closes = historical_data.get('adj_closes', [])
        
        if not adj_closes or len(adj_closes) < 2:
            return Decimal("20.0")  # Default
        
        # Clean data
        adj_closes = [p for p in adj_closes if p is not None]
        
        if len(adj_closes) < 2:
            return Decimal("20.0")
        
        # Calculate drawdowns
        peak = adj_closes[0]
        max_dd = 0
        
        for price in adj_closes:
            if price > peak:
                peak = price
            
            drawdown = (peak - price) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        return Decimal(str(round(max_dd * 100, 2)))
    
    def calculate_correlation_matrix(
        self,
        etf_codes: List[str],
        lookback_days: int = 756  # 3 years
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate correlation matrix for ETFs
        """
        # Fetch historical data for all ETFs
        all_data = {}
        for code in etf_codes:
            hist_data = self.fetch_etf_historical_data(code)
            if hist_data:
                all_data[code] = hist_data
        
        if len(all_data) < 2:
            return {}
        
        # Build returns matrix
        returns_matrix = {}
        
        for code, data in all_data.items():
            adj_closes = data.get('adj_closes', [])
            if not adj_closes or len(adj_closes) < 2:
                continue
            
            # Calculate daily returns
            daily_returns = []
            for i in range(1, min(len(adj_closes), lookback_days)):
                if adj_closes[i-1] and adj_closes[i-1] > 0:
                    ret = (adj_closes[i] - adj_closes[i-1]) / adj_closes[i-1]
                    daily_returns.append(ret)
            
            returns_matrix[code] = daily_returns
        
        # Calculate correlation
        correlation_matrix = {}
        
        for code1 in returns_matrix:
            correlation_matrix[code1] = {}
            
            for code2 in returns_matrix:
                if code1 == code2:
                    correlation_matrix[code1][code2] = Decimal("1.0")
                else:
                    # Calculate correlation
                    returns1 = returns_matrix[code1]
                    returns2 = returns_matrix[code2]
                    
                    # Align lengths
                    min_len = min(len(returns1), len(returns2))
                    returns1 = returns1[:min_len]
                    returns2 = returns2[:min_len]
                    
                    if len(returns1) > 10:
                        corr = np.corrcoef(returns1, returns2)[0, 1]
                        correlation_matrix[code1][code2] = Decimal(str(round(corr, 3)))
                    else:
                        correlation_matrix[code1][code2] = Decimal("0.5")  # Default
        
        return correlation_matrix
    
    def build_etf_from_yahoo_data(
        self,
        etf_code: str,
        asset_class: AssetClass,
        category: ETFCategory
    ) -> Optional[ETF]:
        """
        Build ETF object from Yahoo Finance data
        """
        # Fetch profile
        profile = self.fetch_etf_profile(etf_code)
        if not profile:
            return None
        
        # Fetch historical data
        historical_data = self.fetch_etf_historical_data(etf_code)
        if not historical_data:
            return None
        
        # Calculate metrics
        returns = self.calculate_returns(historical_data)
        volatility = self.calculate_volatility(historical_data)
        sharpe_ratio = self.calculate_sharpe_ratio(returns, volatility)
        max_drawdown = self.calculate_max_drawdown(historical_data)
        
        # Build ETF object
        etf = ETF(
            etf_code=profile['etf_code'],
            etf_name=profile['etf_name'],
            provider=profile['provider'],
            asset_class=asset_class,
            category=category,
            expense_ratio=profile.get('expense_ratio', Decimal("0.20")),
            aum=profile.get('aum', Decimal("100000000")),
            avg_daily_volume=Decimal("1000000"),  # Default
            inception_date=historical_data.get('start_date', date(2010, 1, 1)),
            franking_yield=self._estimate_franking_yield(asset_class),
            distribution_yield=Decimal("2.0"),  # Default
            returns_1y=returns.get('returns_1y'),
            returns_3y=returns.get('returns_3y'),
            returns_5y=returns.get('returns_5y'),
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown
        )
        
        logger.info(f"Built ETF from Yahoo data: {etf_code}")
        return etf
    
    def fetch_full_australian_etf_universe(self) -> List[ETF]:
        """
        Fetch full Australian ETF universe from Yahoo Finance
        """
        logger.info("Fetching full Australian ETF universe from Yahoo Finance...")
        
        etf_universe = []
        
        # Map ETF codes to asset classes and categories
        etf_mapping = {
            # Australian Equity - Large Cap
            "VAS.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP),
            "IOZ.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP),
            "A200.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP),
            "STW.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP),
            "VHY.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_LARGE_CAP),
            
            # Australian Equity - Small Cap
            "VSO.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_SMALL_CAP),
            "SMLL.AX": (AssetClass.AUSTRALIAN_EQUITY, ETFCategory.AUSTRALIAN_SHARES_SMALL_CAP),
            
            # International Equity - Developed
            "VGS.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_DEVELOPED),
            "IVV.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_DEVELOPED),
            "VTS.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_DEVELOPED),
            "IWLD.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_DEVELOPED),
            "NDQ.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_DEVELOPED),
            "HNDQ.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_DEVELOPED),
            
            # International Equity - Emerging
            "VGE.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_EMERGING),
            "IEM.AX": (AssetClass.INTERNATIONAL_EQUITY, ETFCategory.INTERNATIONAL_SHARES_EMERGING),
            
            # Australian Bonds
            "VAF.AX": (AssetClass.FIXED_INCOME, ETFCategory.AUSTRALIAN_BONDS),
            "VGB.AX": (AssetClass.FIXED_INCOME, ETFCategory.AUSTRALIAN_BONDS),
            "BOND.AX": (AssetClass.FIXED_INCOME, ETFCategory.AUSTRALIAN_BONDS),
            
            # Cash
            "BILL.AX": (AssetClass.CASH, ETFCategory.CASH_ENHANCED),
            "AAA.AX": (AssetClass.CASH, ETFCategory.CASH_ENHANCED),
        }
        
        for etf_code, (asset_class, category) in etf_mapping.items():
            etf = self.build_etf_from_yahoo_data(etf_code, asset_class, category)
            if etf:
                etf_universe.append(etf)
        
        logger.info(f"Fetched {len(etf_universe)} ETFs from Yahoo Finance")
        return etf_universe
    
    def _extract_provider(self, etf_name: str) -> str:
        """Extract provider from ETF name"""
        if "Vanguard" in etf_name:
            return "Vanguard"
        elif "iShares" in etf_name:
            return "iShares"
        elif "BetaShares" in etf_name:
            return "BetaShares"
        elif "SPDR" in etf_name:
            return "SPDR"
        elif "VanEck" in etf_name:
            return "VanEck"
        else:
            return "Other"
    
    def _extract_decimal(self, value_dict: Dict) -> Decimal:
        """Extract decimal from Yahoo Finance value dict"""
        if isinstance(value_dict, dict):
            raw_value = value_dict.get('raw', 0)
            return Decimal(str(raw_value))
        return Decimal("0")
    
    def _estimate_franking_yield(self, asset_class: AssetClass) -> Decimal:
        """Estimate franking yield based on asset class"""
        if asset_class == AssetClass.AUSTRALIAN_EQUITY:
            return Decimal("3.0")  # Australian equities typically 3%
        else:
            return Decimal("0.0")  # International assets don't have franking
