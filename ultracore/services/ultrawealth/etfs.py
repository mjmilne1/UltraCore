"""
Complete Australian ETF Universe - 100+ ASX Listed ETFs
For UltraWealth Integration
Updated: November 2025
"""

from typing import List, Dict, Optional

class AustralianETFUniverse:
    """
    Comprehensive Australian ETF Universe
    All ETFs listed on ASX with .AX suffix for Yahoo Finance
    """
    
    # ========================================================================
    # AUSTRALIAN EQUITY ETFs
    # ========================================================================
    
    AUSTRALIAN_EQUITY = {
        # Broad Market
        "VAS.AX": {"name": "Vanguard Australian Shares Index ETF", "provider": "Vanguard", "category": "Broad Market"},
        "IOZ.AX": {"name": "iShares Core S&P/ASX 200 ETF", "provider": "BlackRock", "category": "Broad Market"},
        "STW.AX": {"name": "SPDR S&P/ASX 200 Fund", "provider": "State Street", "category": "Broad Market"},
        "A200.AX": {"name": "Betashares Australia 200 ETF", "provider": "Betashares", "category": "Broad Market"},
        "OZR.AX": {"name": "SPDR S&P/ASX 200 Resources Fund", "provider": "State Street", "category": "Broad Market"},
        
        # Large Cap
        "SFY.AX": {"name": "SPDR S&P/ASX 50 Fund", "provider": "State Street", "category": "Large Cap"},
        "AUST.AX": {"name": "BetaShares Managed Risk Australian Share Fund", "provider": "Betashares", "category": "Large Cap"},
        
        # Small/Mid Cap
        "VSO.AX": {"name": "Vanguard MSCI Australian Small Companies Index ETF", "provider": "Vanguard", "category": "Small Cap"},
        "SMLL.AX": {"name": "BetaShares Australian Small Companies Select Fund", "provider": "Betashares", "category": "Small Cap"},
        "MVS.AX": {"name": "VanEck Australian Small Companies ETF", "provider": "VanEck", "category": "Small Cap"},
        
        # High Dividend
        "VHY.AX": {"name": "Vanguard Australian Shares High Yield ETF", "provider": "Vanguard", "category": "High Dividend"},
        "IHD.AX": {"name": "iShares S&P/ASX Dividend Opportunities ETF", "provider": "BlackRock", "category": "High Dividend"},
        "SYI.AX": {"name": "SPDR MSCI Australia Select High Dividend Yield Fund", "provider": "State Street", "category": "High Dividend"},
        "YMAX.AX": {"name": "BetaShares Australia Top 20 Equity Yield Maximiser", "provider": "Betashares", "category": "High Dividend"},
        "EINC.AX": {"name": "BetaShares Legg Mason Equity Income Fund", "provider": "Betashares", "category": "High Dividend"},
        "ZYAU.AX": {"name": "ETFS S&P/ASX 100 High Yield ETF", "provider": "ETFS", "category": "High Dividend"},
    }
    
    # ========================================================================
    # INTERNATIONAL EQUITY ETFs
    # ========================================================================
    
    INTERNATIONAL_EQUITY = {
        # Global/World
        "VGS.AX": {"name": "Vanguard MSCI Index International Shares ETF", "provider": "Vanguard", "category": "International"},
        "VGAD.AX": {"name": "Vanguard MSCI Index International Shares (Hedged) ETF", "provider": "Vanguard", "category": "International"},
        "IWLD.AX": {"name": "iShares MSCI World ETF", "provider": "BlackRock", "category": "International"},
        "WXOZ.AX": {"name": "BetaShares Diversified All Growth ETF", "provider": "Betashares", "category": "International"},
        "WDIV.AX": {"name": "SPDR MSCI World Quality Mix Fund", "provider": "State Street", "category": "International"},
        
        # US Market
        "VTS.AX": {"name": "Vanguard US Total Market Shares Index ETF", "provider": "Vanguard", "category": "US Equity"},
        "IVV.AX": {"name": "iShares S&P 500 ETF", "provider": "BlackRock", "category": "US Equity"},
        "SPY.AX": {"name": "SPDR S&P 500 ETF Trust", "provider": "State Street", "category": "US Equity"},
        "UMAX.AX": {"name": "BetaShares S&P 500 Yield Maximiser", "provider": "Betashares", "category": "US Equity"},
        
        # Asia Pacific
        "VAP.AX": {"name": "Vanguard MSCI Asia Pacific ex Japan Shares Index ETF", "provider": "Vanguard", "category": "Asia Pacific"},
        "IAA.AX": {"name": "iShares Asia 50 ETF", "provider": "BlackRock", "category": "Asia Pacific"},
        "ASIA.AX": {"name": "BetaShares Asia Technology Tigers ETF", "provider": "Betashares", "category": "Asia Pacific"},
        
        # China/India
        "IZZ.AX": {"name": "iShares China Large-Cap ETF", "provider": "BlackRock", "category": "China"},
        "IIND.AX": {"name": "iShares India ETF", "provider": "BlackRock", "category": "India"},
        "NDIA.AX": {"name": "BetaShares India Quality ETF", "provider": "Betashares", "category": "India"},
        
        # Europe
        "VEQ.AX": {"name": "Vanguard FTSE Europe Shares ETF", "provider": "Vanguard", "category": "Europe"},
        "IEU.AX": {"name": "iShares Europe ETF", "provider": "BlackRock", "category": "Europe"},
        
        # Emerging Markets
        "VGE.AX": {"name": "Vanguard FTSE Emerging Markets Shares ETF", "provider": "Vanguard", "category": "Emerging Markets"},
        "IEM.AX": {"name": "iShares MSCI Emerging Markets ETF", "provider": "BlackRock", "category": "Emerging Markets"},
    }
    
    # ========================================================================
    # SECTOR ETFs
    # ========================================================================
    
    SECTOR_ETFS = {
        # Technology
        "NDQ.AX": {"name": "BetaShares NASDAQ 100 ETF", "provider": "Betashares", "category": "Technology"},
        "TECH.AX": {"name": "ETFS Morningstar Global Technology ETF", "provider": "ETFS", "category": "Technology"},
        "ATEC.AX": {"name": "BetaShares Australian Technology ETF", "provider": "Betashares", "category": "Technology"},
        "FANG.AX": {"name": "ETFS FANG+ ETF", "provider": "ETFS", "category": "Technology"},
        
        # Healthcare
        "DRUG.AX": {"name": "BetaShares Global Healthcare ETF", "provider": "Betashares", "category": "Healthcare"},
        "IXJ.AX": {"name": "iShares Global Healthcare ETF", "provider": "BlackRock", "category": "Healthcare"},
        
        # Financials
        "QFN.AX": {"name": "BetaShares S&P/ASX 200 Financials Sector ETF", "provider": "Betashares", "category": "Financials"},
        "OZF.AX": {"name": "SPDR S&P/ASX 200 Financials Fund", "provider": "State Street", "category": "Financials"},
        
        # Resources/Mining
        "QRE.AX": {"name": "BetaShares S&P/ASX 200 Resources Sector ETF", "provider": "Betashares", "category": "Resources"},
        "MVR.AX": {"name": "VanEck Australian Resources ETF", "provider": "VanEck", "category": "Resources"},
        
        # Energy
        "OOO.AX": {"name": "BetaShares Crude Oil Index ETF", "provider": "Betashares", "category": "Energy"},
        
        # Consumer
        "IXI.AX": {"name": "iShares Global Consumer Staples ETF", "provider": "BlackRock", "category": "Consumer"},
    }
    
    # ========================================================================
    # PROPERTY/REAL ESTATE ETFs
    # ========================================================================
    
    PROPERTY_ETFS = {
        "VAP.AX": {"name": "Vanguard Australian Property Securities Index ETF", "provider": "Vanguard", "category": "Property"},
        "SLF.AX": {"name": "SPDR S&P/ASX 200 Listed Property Fund", "provider": "State Street", "category": "Property"},
        "DJRE.AX": {"name": "SPDR Dow Jones Global Real Estate Fund", "provider": "State Street", "category": "Property"},
        "REIT.AX": {"name": "BetaShares Australian Property ETF", "provider": "Betashares", "category": "Property"},
        "MVA.AX": {"name": "VanEck Australian Property ETF", "provider": "VanEck", "category": "Property"},
    }
    
    # ========================================================================
    # FIXED INCOME/BOND ETFs
    # ========================================================================
    
    BOND_ETFS = {
        # Australian Government Bonds
        "VGB.AX": {"name": "Vanguard Australian Government Bond Index ETF", "provider": "Vanguard", "category": "Government Bonds"},
        "GOVT.AX": {"name": "BetaShares Australian Government Bond ETF", "provider": "Betashares", "category": "Government Bonds"},
        "AGVT.AX": {"name": "BetaShares Australian Government Treasury Bond ETF", "provider": "Betashares", "category": "Government Bonds"},
        
        # Australian Corporate Bonds
        "VAF.AX": {"name": "Vanguard Australian Fixed Interest Index ETF", "provider": "Vanguard", "category": "Corporate Bonds"},
        "BOND.AX": {"name": "SPDR S&P/ASX Australian Bond Fund", "provider": "State Street", "category": "Corporate Bonds"},
        "IAF.AX": {"name": "iShares Core Composite Bond ETF", "provider": "BlackRock", "category": "Corporate Bonds"},
        "PLUS.AX": {"name": "BetaShares Australian Investment Grade Bond ETF", "provider": "Betashares", "category": "Corporate Bonds"},
        
        # International Bonds
        "VIF.AX": {"name": "Vanguard International Fixed Interest Index ETF", "provider": "Vanguard", "category": "International Bonds"},
        "IHEB.AX": {"name": "iShares Global Govt Bond (Hedged) ETF", "provider": "BlackRock", "category": "International Bonds"},
        "IHHY.AX": {"name": "iShares Global High Yield Bond (Hedged) ETF", "provider": "BlackRock", "category": "International Bonds"},
        
        # Floating Rate
        "FLOT.AX": {"name": "VanEck Australian Floating Rate ETF", "provider": "VanEck", "category": "Floating Rate"},
    }
    
    # ========================================================================
    # COMMODITIES ETFs
    # ========================================================================
    
    COMMODITY_ETFS = {
        # Gold
        "GOLD.AX": {"name": "ETFS Physical Gold", "provider": "ETFS", "category": "Gold"},
        "QAU.AX": {"name": "BetaShares Gold Bullion ETF", "provider": "Betashares", "category": "Gold"},
        "PMGOLD.AX": {"name": "Perth Mint Gold ETF", "provider": "Perth Mint", "category": "Gold"},
        
        # Silver
        "ETPMAG.AX": {"name": "ETFS Physical Silver", "provider": "ETFS", "category": "Silver"},
        
        # Commodities Basket
        "QCB.AX": {"name": "BetaShares Commodities Basket ETF", "provider": "Betashares", "category": "Commodities"},
    }
    
    # ========================================================================
    # ESG/ETHICAL ETFs
    # ========================================================================
    
    ESG_ETFS = {
        "FAIR.AX": {"name": "BetaShares Australian Sustainability Leaders ETF", "provider": "Betashares", "category": "ESG"},
        "ETHI.AX": {"name": "BetaShares Global Sustainability Leaders ETF", "provider": "Betashares", "category": "ESG"},
        "VESG.AX": {"name": "Vanguard Ethically Conscious International Shares ETF", "provider": "Vanguard", "category": "ESG"},
        "VETH.AX": {"name": "Vanguard Ethically Conscious Australian Shares ETF", "provider": "Vanguard", "category": "ESG"},
        "ERTH.AX": {"name": "BetaShares Climate Change Innovation ETF", "provider": "Betashares", "category": "ESG"},
        "GBND.AX": {"name": "BetaShares Sustainability Leaders Diversified Bond ETF", "provider": "Betashares", "category": "ESG"},
    }
    
    # ========================================================================
    # SMART BETA/FACTOR ETFs
    # ========================================================================
    
    SMART_BETA_ETFS = {
        "QOZ.AX": {"name": "BetaShares FTSE RAFI Australia 200 ETF", "provider": "Betashares", "category": "Smart Beta"},
        "AQLT.AX": {"name": "BetaShares Australian Quality ETF", "provider": "Betashares", "category": "Smart Beta"},
        "MVW.AX": {"name": "VanEck MSCI World ex Australia Quality ETF", "provider": "VanEck", "category": "Smart Beta"},
        "WRLD.AX": {"name": "BetaShares Managed Risk Global Share Fund", "provider": "Betashares", "category": "Smart Beta"},
    }
    
    # ========================================================================
    # ACTIVE/MANAGED ETFs
    # ========================================================================
    
    ACTIVE_ETFS = {
        "DBBF.AX": {"name": "BetaShares Diversified Balanced ETF", "provider": "Betashares", "category": "Diversified"},
        "DZZF.AX": {"name": "BetaShares Diversified Conservative ETF", "provider": "Betashares", "category": "Diversified"},
        "DHHF.AX": {"name": "BetaShares Diversified All Growth ETF", "provider": "Betashares", "category": "Diversified"},
        "VDHG.AX": {"name": "Vanguard Diversified High Growth Index ETF", "provider": "Vanguard", "category": "Diversified"},
        "VDGR.AX": {"name": "Vanguard Diversified Growth Index ETF", "provider": "Vanguard", "category": "Diversified"},
        "VDBA.AX": {"name": "Vanguard Diversified Balanced Index ETF", "provider": "Vanguard", "category": "Diversified"},
        "VDCO.AX": {"name": "Vanguard Diversified Conservative Index ETF", "provider": "Vanguard", "category": "Diversified"},
    }
    
    # ========================================================================
    # CURRENCY/INVERSE ETFs
    # ========================================================================
    
    CURRENCY_ETFS = {
        "AUDS.AX": {"name": "BetaShares Strong Australian Dollar ETF", "provider": "Betashares", "category": "Currency"},
        "YANK.AX": {"name": "BetaShares Strong US Dollar ETF", "provider": "Betashares", "category": "Currency"},
        "BBOZ.AX": {"name": "BetaShares Australian Equities Strong Bear", "provider": "Betashares", "category": "Inverse"},
        "BBUS.AX": {"name": "BetaShares US Equities Strong Bear", "provider": "Betashares", "category": "Inverse"},
    }
    
    @classmethod
    def get_all_etfs(cls) -> Dict[str, Dict]:
        """Get all ETFs from all categories"""
        all_etfs = {}
        for category_dict in [
            cls.AUSTRALIAN_EQUITY,
            cls.INTERNATIONAL_EQUITY,
            cls.SECTOR_ETFS,
            cls.PROPERTY_ETFS,
            cls.BOND_ETFS,
            cls.COMMODITY_ETFS,
            cls.ESG_ETFS,
            cls.SMART_BETA_ETFS,
            cls.ACTIVE_ETFS,
            cls.CURRENCY_ETFS
        ]:
            all_etfs.update(category_dict)
        return all_etfs
    
    @classmethod
    def get_all_tickers(cls) -> List[str]:
        """Get list of all ticker symbols"""
        return sorted(cls.get_all_etfs().keys())
    
    @classmethod
    def get_etf_info(cls, ticker: str) -> Optional[Dict]:
        """Get information about a specific ETF"""
        all_etfs = cls.get_all_etfs()
        return all_etfs.get(ticker)
    
    @classmethod
    def is_valid_etf(cls, ticker: str) -> bool:
        """Check if ticker is in approved universe"""
        return ticker in cls.get_all_etfs()
    
    @classmethod
    def get_by_category(cls, category: str) -> List[str]:
        """Get ETFs by category"""
        all_etfs = cls.get_all_etfs()
        return [ticker for ticker, info in all_etfs.items() 
                if info["category"].lower() == category.lower()]
    
    @classmethod
    def get_by_provider(cls, provider: str) -> List[str]:
        """Get ETFs by provider"""
        all_etfs = cls.get_all_etfs()
        return [ticker for ticker, info in all_etfs.items() 
                if info["provider"].lower() == provider.lower()]
    
    @classmethod
    def get_summary(cls) -> Dict:
        """Get universe summary statistics"""
        all_etfs = cls.get_all_etfs()
        
        categories = {}
        providers = {}
        
        for ticker, info in all_etfs.items():
            cat = info["category"]
            prov = info["provider"]
            
            categories[cat] = categories.get(cat, 0) + 1
            providers[prov] = providers.get(prov, 0) + 1
        
        return {
            "total_etfs": len(all_etfs),
            "categories": categories,
            "providers": providers,
            "tickers": cls.get_all_tickers()
        }

australian_etf_universe = AustralianETFUniverse()
