"""
UltraWealth Australian ETF Universe
Curated list of Australian listed ETFs for wealth management
"""

from typing import List, Dict, Optional

class AustralianETFUniverse:
    """
    Australian ETF Universe - ASX Listed ETFs Only
    All tickers use .AX suffix for Yahoo Finance
    """
    
    # Major Australian ETFs by Category
    EQUITY_ETFS = {
        # Broad Market
        "VAS.AX": {"name": "Vanguard Australian Shares Index ETF", "category": "Broad Market", "provider": "Vanguard"},
        "IOZ.AX": {"name": "iShares Core S&P/ASX 200 ETF", "category": "Broad Market", "provider": "BlackRock"},
        "STW.AX": {"name": "SPDR S&P/ASX 200 Fund", "category": "Broad Market", "provider": "State Street"},
        "A200.AX": {"name": "Betashares Australia 200 ETF", "category": "Broad Market", "provider": "Betashares"},
        
        # International Equities
        "VGS.AX": {"name": "Vanguard MSCI Index International Shares ETF", "category": "International", "provider": "Vanguard"},
        "IVV.AX": {"name": "iShares S&P 500 ETF", "category": "International", "provider": "BlackRock"},
        "VTS.AX": {"name": "Vanguard US Total Market Shares Index ETF", "category": "International", "provider": "Vanguard"},
        "IWLD.AX": {"name": "iShares MSCI World ETF", "category": "International", "provider": "BlackRock"},
        
        # Small/Mid Cap
        "VSO.AX": {"name": "Vanguard MSCI Australian Small Companies Index ETF", "category": "Small Cap", "provider": "Vanguard"},
        "SMLL.AX": {"name": "BetaShares Australian Small Companies Select Fund", "category": "Small Cap", "provider": "Betashares"},
    }
    
    BOND_ETFS = {
        # Australian Bonds
        "VAF.AX": {"name": "Vanguard Australian Fixed Interest Index ETF", "category": "Fixed Income", "provider": "Vanguard"},
        "GOVT.AX": {"name": "BetaShares Australian Government Bond ETF", "category": "Fixed Income", "provider": "Betashares"},
        "BOND.AX": {"name": "SPDR S&P/ASX Australian Bond Fund", "category": "Fixed Income", "provider": "State Street"},
        
        # International Bonds
        "VGB.AX": {"name": "Vanguard Australian Government Bond Index ETF", "category": "Fixed Income", "provider": "Vanguard"},
        "IHEB.AX": {"name": "iShares Global Govt Bond (Hedged) ETF", "category": "Fixed Income", "provider": "BlackRock"},
    }
    
    SECTOR_ETFS = {
        # Technology
        "NDQ.AX": {"name": "BetaShares NASDAQ 100 ETF", "category": "Technology", "provider": "Betashares"},
        "TECH.AX": {"name": "ETFS Morningstar Global Technology ETF", "category": "Technology", "provider": "ETFS"},
        
        # Property
        "VAP.AX": {"name": "Vanguard Australian Property Securities Index ETF", "category": "Property", "provider": "Vanguard"},
        "DJRE.AX": {"name": "SPDR Dow Jones Global Real Estate Fund", "category": "Property", "provider": "State Street"},
        
        # Resources
        "QRE.AX": {"name": "BetaShares S&P/ASX 200 Resources Sector ETF", "category": "Resources", "provider": "Betashares"},
    }
    
    SPECIALTY_ETFS = {
        # Ethical/ESG
        "FAIR.AX": {"name": "BetaShares Australian Sustainability Leaders ETF", "category": "ESG", "provider": "Betashares"},
        "ETHI.AX": {"name": "BetaShares Global Sustainability Leaders ETF", "category": "ESG", "provider": "Betashares"},
        
        # High Dividend
        "VHY.AX": {"name": "Vanguard Australian Shares High Yield ETF", "category": "Income", "provider": "Vanguard"},
        "YMAX.AX": {"name": "BetaShares Australia Top 20 Equity Yield Maximiser Fund", "category": "Income", "provider": "Betashares"},
    }
    
    @classmethod
    def get_all_etfs(cls) -> List[str]:
        """Get all approved Australian ETF tickers"""
        all_etfs = []
        all_etfs.extend(cls.EQUITY_ETFS.keys())
        all_etfs.extend(cls.BOND_ETFS.keys())
        all_etfs.extend(cls.SECTOR_ETFS.keys())
        all_etfs.extend(cls.SPECIALTY_ETFS.keys())
        return sorted(all_etfs)
    
    @classmethod
    def get_etf_info(cls, ticker: str) -> Optional[Dict]:
        """Get information about a specific ETF"""
        for etf_dict in [cls.EQUITY_ETFS, cls.BOND_ETFS, cls.SECTOR_ETFS, cls.SPECIALTY_ETFS]:
            if ticker in etf_dict:
                return etf_dict[ticker]
        return None
    
    @classmethod
    def is_valid_etf(cls, ticker: str) -> bool:
        """Check if ticker is in approved universe"""
        return ticker in cls.get_all_etfs()
    
    @classmethod
    def get_by_category(cls, category: str) -> List[str]:
        """Get ETFs by category"""
        result = []
        for etf_dict in [cls.EQUITY_ETFS, cls.BOND_ETFS, cls.SECTOR_ETFS, cls.SPECIALTY_ETFS]:
            for ticker, info in etf_dict.items():
                if info["category"].lower() == category.lower():
                    result.append(ticker)
        return result
    
    @classmethod
    def get_by_provider(cls, provider: str) -> List[str]:
        """Get ETFs by provider"""
        result = []
        for etf_dict in [cls.EQUITY_ETFS, cls.BOND_ETFS, cls.SECTOR_ETFS, cls.SPECIALTY_ETFS]:
            for ticker, info in etf_dict.items():
                if info["provider"].lower() == provider.lower():
                    result.append(ticker)
        return result

# Global instance
australian_etf_universe = AustralianETFUniverse()
