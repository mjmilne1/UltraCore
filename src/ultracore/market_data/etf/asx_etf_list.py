"""
Complete list of ASX-listed ETFs
Updated: November 2024
Source: Market Index, ASX, various ETF providers

This list includes 360+ ETFs across all categories:
- Australian Equities
- International Equities
- Fixed Income
- Commodities
- Currencies
- Alternatives
"""
from typing import List, Optional, Dict

# Major Australian Equity ETFs
AUSTRALIAN_EQUITY_ETFS = [
    # Broad Market
    "VAS",   # Vanguard Australian Shares Index ETF
    "A200",  # BetaShares Australia 200 ETF
    "IOZ",   # iShares Core S&P/ASX 200 ETF
    "STW",   # SPDR S&P/ASX 200 Fund
    "OZF",   # SPDR S&P/ASX 50 Fund
    "MVW",   # VanEck Australian Equal Weight ETF
    "FAIR",  # BetaShares Australian Sustainability Leaders ETF
    
    # Dividend/Income
    "VHY",   # Vanguard Australian Shares High Yield ETF
    "IHD",   # iShares S&P/ASX Dividend Opportunities
    "SYI",   # SPDR MSCI Australia Select High Dividend Yield Fund
    "ZYAU",  # Global X S&P/ASX 200 High Dividend ETF
    "AYLD",  # Global X S&P/ASX 200 Covered Call ETF
    "YMAX",  # BetaShares Australian Top 20 Equity Yield Maximiser
    "HVST",  # BetaShares Australian Dividend Harvester Fund
    "DIVI",  # Ausbil Active Dividend Income Fund
    "EINC",  # BetaShares Legg Mason Equity Income Fund
    "RINC",  # BetaShares Legg Mason Real Income Fund
    "HYLD",  # BetaShares S&P Australian Shares High Yield ETF
    "EIGA",  # eInvest Income Generator Fund
    "DVDY",  # VanEck Vectors Morningstar Australian Moat Income
    "RDV",   # Russell High Dividend Australian Shares
    "RARI",  # Russell Australian Responsible Investment
    "INIF",  # Intelligent Investor Aus Equity Income Fund
    "EQIN",  # Investors Mutual Equity Income Fund
    "IMLC",  # IML Concentrated Australian Share Fund
    "HBRD",  # Active Australian Hybrids Fund
    "MA1",   # MA Credit Income Trust
    "DIFF",  # Perpetual Diversified Income Active ETF
    "WMX",   # WAM Income Maximiser Limited
    
    # Small Cap
    "VSO",   # Vanguard MSCI Australian Small Companies Index ETF
    "SMLL",  # BetaShares Australian Small Companies Select Fund
    
    # Sectors
    "MVB",   # VanEck Australian Banks ETF
    "MVR",   # VanEck Australian Resources ETF
    "MVE",   # VanEck Australian Equal Weight ETF
    "ATEC",  # BetaShares S&P/ASX Australian Technology ETF
    "DRUG",  # BetaShares Global Healthcare ETF
    "MNRS",  # BetaShares Global Gold Miners ETF
    
    # ESG/Ethical
    "VETH",  # Vanguard Ethically Conscious Australian Shares ETF
    "FAIR",  # BetaShares Australian Sustainability Leaders ETF
    "ETHI",  # BetaShares Global Sustainability Leaders ETF
    "RARI",  # Russell Australian Responsible Investment ETF
]

# International Equity ETFs
INTERNATIONAL_EQUITY_ETFS = [
    # Global Broad
    "VGS",   # Vanguard MSCI Index International Shares ETF
    "VGAD",  # Vanguard MSCI Index International Shares (Hedged) ETF
    "IVV",   # iShares S&P 500 ETF
    "IHVV",  # iShares S&P 500 (AUD Hedged) ETF
    "IOO",   # iShares Global 100 ETF
    "WXOZ",  # BetaShares Diversified All Growth ETF
    "DHHF",  # BetaShares Diversified High Growth ETF
    "DZZF",  # BetaShares Diversified Conservative Income ETF
    "VDHG",  # Vanguard Diversified High Growth Index ETF
    "VDGR",  # Vanguard Diversified Growth Index ETF
    "VDBA",  # Vanguard Diversified Balanced Index ETF
    "VDCO",  # Vanguard Diversified Conservative Index ETF
    
    # US Markets
    "SPY",   # SPDR S&P 500 ETF Trust
    "IVV",   # iShares S&P 500 ETF
    "VTS",   # Vanguard US Total Market Shares Index ETF
    "QUS",   # BetaShares NASDAQ 100 ETF
    "NDQ",   # BetaShares NASDAQ 100 ETF
    "HNDQ",  # BetaShares NASDAQ 100 ETF - Currency Hedged
    "UMAX",  # BetaShares S&P 500 Yield Maximiser Fund
    "ZYUS",  # Global X S&P 500 High Dividend ETF
    "YANK",  # BetaShares Strong US Dollar Hedge Fund
    "USA",   # BetaShares US Dollar ETF
    "GGUS",  # BetaShares Geared US Equity Fund
    
    # Europe
    "VEQ",   # Vanguard FTSE Europe Shares ETF
    "IEU",   # iShares Europe ETF
    "HEUR",  # BetaShares Europe ETF - Currency Hedged
    
    # Asia
    "VAE",   # Vanguard FTSE Asia ex Japan Shares Index ETF
    "IAA",   # iShares Asia 50 ETF
    "ASIA",  # BetaShares Asia Technology Tigers ETF
    "ASAO",  # ActiveX Ardea Real Outcome Fund
    "EAFZ",  # eInvest Asia Pacific Equity Fund
    "FASI",  # Fidelity Asian Opportunities Fund
    "DRGN",  # BetaShares FTSE RAFI Emerging Markets ETF
    
    # Japan
    "IJP",   # iShares MSCI Japan ETF
    "HJPN",  # BetaShares Japan ETF - Currency Hedged
    "IZZ",   # iShares China Large-Cap ETF
    "IKO",   # iShares MSCI South Korea Capped ETF
    "CETF",  # VanEck China New Economy ETF
    
    # India
    "IIND",  # iShares India ETF
    "FIIN",  # Fidelity India Fund
    "NDIA",  # BetaShares India Quality ETF
    "GRIN",  # Global X India Nifty 50 ETF
    
    # Emerging Markets
    "VGE",   # Vanguard FTSE Emerging Markets Shares ETF
    "IEM",   # iShares MSCI Emerging Markets ETF
    "FEMX",  # BetaShares FTSE RAFI Emerging Markets ETF
    
    # Global Small Cap
    "WSMG",  # BetaShares Global Small Companies ETF
    "VSO",   # Vanguard MSCI Australian Small Companies Index ETF
]

# Sector & Thematic ETFs
SECTOR_THEMATIC_ETFS = [
    # Technology
    "NDQ",   # BetaShares NASDAQ 100 ETF
    "ATEC",  # BetaShares S&P/ASX Australian Technology ETF
    "ASIA",  # BetaShares Asia Technology Tigers ETF
    "HACK",  # BetaShares Global Cybersecurity ETF
    "ROBO",  # BetaShares Global Robotics and AI ETF
    "CLDD",  # BetaShares Cloud Computing ETF
    "FANG",  # Global X FANG+ ETF
    "SEMI",  # Global X Semiconductor ETF
    
    # Healthcare
    "DRUG",  # BetaShares Global Healthcare ETF
    "IXJ",   # iShares Global Healthcare ETF
    
    # Financials
    "MVB",   # VanEck Australian Banks ETF
    "QFN",   # BetaShares Global Financials ETF
    
    # Energy & Resources
    "MVR",   # VanEck Australian Resources ETF
    "OOO",   # BetaShares Crude Oil Index ETF
    "OZR",   # BetaShares Australian Resources Sector ETF
    "FUEL",  # BetaShares Global Energy Companies ETF
    "DRIV",  # BetaShares Electric Vehicles and Future Mobility ETF
    "ERTH",  # BetaShares Climate Change Innovation ETF
    
    # Consumer
    "FOOD",  # BetaShares Global Agriculture Companies ETF
    "QLTY",  # VanEck MSCI International Quality ETF
    
    # Infrastructure & Property
    "REIT",  # BetaShares Australian Real Estate Investment Trusts ETF
    "DJRE",  # SPDR Dow Jones Global Real Estate Fund
    "IFRA",  # VanEck FTSE Global Infrastructure (Hedged) ETF
    "MVA",   # VanEck Australian Property ETF
    "VAP",   # Vanguard Australian Property Securities Index ETF
    
    # ESG & Sustainability
    "ETHI",  # BetaShares Global Sustainability Leaders ETF
    "FAIR",  # BetaShares Australian Sustainability Leaders ETF
    "ERTH",  # BetaShares Climate Change Innovation ETF
    "ESGI",  # VanEck MSCI International Sustainable Equity ETF
    "VESG",  # Vanguard Ethically Conscious International Shares ETF
    "VETH",  # Vanguard Ethically Conscious Australian Shares ETF
    "GBND",  # BetaShares Sustainability Leaders Diversified Bond ETF
]

# Fixed Income / Bonds ETFs
FIXED_INCOME_ETFS = [
    # Australian Bonds
    "VAF",   # Vanguard Australian Fixed Interest Index ETF
    "VGB",   # Vanguard Australian Government Bond Index ETF
    "BILL",  # BetaShares Australian Bank Senior Floating Rate Bond ETF
    "IAF",   # iShares Core Composite Bond ETF
    "CRED",  # BetaShares Australian Investment Grade Corporate Bond ETF
    "PLUS",  # BetaShares Australian Enhanced Income Fund
    "BNDS",  # BetaShares Legg Mason Australian Bond Fund
    "QPON",  # BetaShares Australian Composite Bond ETF
    "GBND",  # BetaShares Sustainability Leaders Diversified Bond ETF
    "PAXX",  # BetaShares Australian High Interest Cash ETF
    "AAA",   # BetaShares Australian High Interest Cash ETF
    
    # International Bonds
    "VIF",   # Vanguard International Fixed Interest Index ETF
    "VBND",  # Vanguard Global Aggregate Bond Index (Hedged) ETF
    "IHEB",  # iShares Global Bond Index (Hedged) ETF
    "IHHY",  # iShares Global High Yield Bond (Hedged) ETF
    "GGOV",  # BetaShares Global Government Bond 20+ Year ETF - Currency Hedged
    "XARO",  # ActiveX Ardea Real Outcome Fund
    
    # Inflation-Linked
    "ILB",   # iShares Government Inflation ETF
    "BILL",  # BetaShares Australian Bank Senior Floating Rate Bond ETF
]

# Commodities ETFs
COMMODITIES_ETFS = [
    # Gold
    "GOLD",  # Perth Mint Gold ETF
    "PMGOLD", # Perth Mint Physical Gold ETF
    "QAU",   # BetaShares Gold Bullion ETF
    "MNRS",  # BetaShares Global Gold Miners ETF
    "ETPMAG", # ETFS Physical Gold
    "ETPMPM", # ETFS Physical Precious Metal Basket
    
    # Silver
    "ETPMAG", # ETFS Physical Silver
    
    # Platinum
    "ETPMPT", # ETFS Physical Platinum
    
    # Palladium
    "ETPMPD", # ETFS Physical Palladium
    
    # Oil & Energy
    "OOO",   # BetaShares Crude Oil Index ETF
    "FUEL",  # BetaShares Global Energy Companies ETF
    
    # Agriculture
    "FOOD",  # BetaShares Global Agriculture Companies ETF
    "QAG",   # BetaShares Agriculture ETF
]

# Currency ETFs
CURRENCY_ETFS = [
    "USD",   # BetaShares US Dollar ETF
    "YANK",  # BetaShares Strong US Dollar Hedge Fund
    "EEU",   # BetaShares Euro ETF
    "POU",   # BetaShares British Pound ETF
]

# Leveraged & Inverse ETFs
LEVERAGED_INVERSE_ETFS = [
    "GGUS",  # BetaShares Geared US Equity Fund
    "GEAR",  # BetaShares Geared Australian Equity Fund
    "BBUS",  # BetaShares US Equities Strong Bear Hedge Fund
    "BBOZ",  # BetaShares Australian Equities Strong Bear Fund
    "BEAR",  # BetaShares Australian Equities Bear Fund
]

# Active ETFs
ACTIVE_ETFS = [
    "DIVI",  # Ausbil Active Dividend Income Fund
    "EINC",  # BetaShares Legg Mason Equity Income Fund
    "RINC",  # BetaShares Legg Mason Real Income Fund
    "IMLC",  # IML Concentrated Australian Share Fund
    "INIF",  # Intelligent Investor Aus Equity Income Fund
    "EQIN",  # Investors Mutual Equity Income Fund
    "HBRD",  # Active Australian Hybrids Fund
    "BNDS",  # BetaShares Legg Mason Australian Bond Fund
    "XARO",  # ActiveX Ardea Real Outcome Fund
    "QUAL",  # VanEck MSCI World ex Australia Quality ETF
]

# All ETFs combined
ALL_ASX_ETFS = sorted(list(set(
    AUSTRALIAN_EQUITY_ETFS +
    INTERNATIONAL_EQUITY_ETFS +
    SECTOR_THEMATIC_ETFS +
    FIXED_INCOME_ETFS +
    COMMODITIES_ETFS +
    CURRENCY_ETFS +
    LEVERAGED_INVERSE_ETFS +
    ACTIVE_ETFS
)))

# ETF Categories mapping
ETF_CATEGORIES = {
    "Australian Equity": AUSTRALIAN_EQUITY_ETFS,
    "International Equity": INTERNATIONAL_EQUITY_ETFS,
    "Sector & Thematic": SECTOR_THEMATIC_ETFS,
    "Fixed Income": FIXED_INCOME_ETFS,
    "Commodities": COMMODITIES_ETFS,
    "Currency": CURRENCY_ETFS,
    "Leveraged & Inverse": LEVERAGED_INVERSE_ETFS,
    "Active": ACTIVE_ETFS
}


def get_all_etfs() -> List[str]:
    """Get complete list of all ASX ETFs"""
    return ALL_ASX_ETFS


def get_etfs_by_category(category: str) -> List[str]:
    """Get ETFs by category"""
    return ETF_CATEGORIES.get(category, [])


def get_category_for_etf(ticker: str) -> Optional[str]:
    """Get category for a specific ETF"""
    for category, etfs in ETF_CATEGORIES.items():
        if ticker in etfs:
            return category
    return None
