"""
UltraWealth Integration Service
Connects Yahoo Finance data to UltraWealth with Australian ETF restrictions
"""

from typing import List, Dict, Any, Optional
from ultracore.services.yahoo_finance import yahoo_service, ml_pipeline, mcp_tools
from ultracore.services.ultrawealth.australian_etfs import australian_etf_universe

class UltraWealthFinancialService:
    """
    Financial service for UltraWealth - Australian ETFs only
    """
    
    def __init__(self):
        self.universe = australian_etf_universe
    
    def validate_ticker(self, ticker: str) -> bool:
        """Validate ticker is in approved Australian ETF universe"""
        if not self.universe.is_valid_etf(ticker):
            raise ValueError(
                f"Ticker {ticker} not in UltraWealth approved universe. "
                f"Must be Australian listed ETF."
            )
        return True
    
    async def get_etf_price(self, ticker: str) -> Dict[str, Any]:
        """Get current price for Australian ETF"""
        self.validate_ticker(ticker)
        data = await yahoo_service.get_company_data(ticker)
        etf_info = self.universe.get_etf_info(ticker)
        
        return {
            "ticker": ticker,
            "name": etf_info["name"],
            "category": etf_info["category"],
            "provider": etf_info["provider"],
            "price": data["market_data"]["current_price"],
            "market_cap": data["market_data"]["market_cap"],
            "volume": data["market_data"]["volume"],
        }
    
    async def get_portfolio_prices(self, tickers: List[str]) -> Dict[str, float]:
        """Get prices for multiple Australian ETFs"""
        # Validate all tickers
        for ticker in tickers:
            self.validate_ticker(ticker)
        
        # Get prices
        prices = await yahoo_service.batch_get_prices(tickers)
        return prices
    
    async def get_etf_prediction(self, ticker: str) -> Dict[str, Any]:
        """Get ML prediction for Australian ETF"""
        self.validate_ticker(ticker)
        
        # Train model if needed
        await ml_pipeline.train_price_predictor(ticker)
        
        # Get prediction
        predicted = await ml_pipeline.predict_next_price(ticker)
        
        # Get current price
        current_data = await yahoo_service.get_company_data(ticker)
        current = current_data["market_data"]["current_price"]
        
        etf_info = self.universe.get_etf_info(ticker)
        
        return {
            "ticker": ticker,
            "name": etf_info["name"],
            "category": etf_info["category"],
            "current_price": current,
            "predicted_price": predicted,
            "change_percent": ((predicted - current) / current * 100) if current else 0,
            "signal": self._get_signal(predicted, current)
        }
    
    def _get_signal(self, predicted: float, current: float) -> str:
        """Generate trading signal"""
        change = ((predicted - current) / current * 100) if current else 0
        
        if change > 5:
            return "STRONG_BUY"
        elif change > 2:
            return "BUY"
        elif change > -2:
            return "HOLD"
        elif change > -5:
            return "SELL"
        else:
            return "STRONG_SELL"
    
    def get_universe_summary(self) -> Dict[str, Any]:
        """Get summary of available ETFs"""
        all_etfs = self.universe.get_all_etfs()
        
        return {
            "total_etfs": len(all_etfs),
            "categories": {
                "Broad Market": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "Broad Market"]),
                "International": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "International"]),
                "Fixed Income": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "Fixed Income"]),
                "Technology": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "Technology"]),
                "Property": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "Property"]),
                "ESG": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "ESG"]),
                "Income": len([e for e in all_etfs if self.universe.get_etf_info(e)["category"] == "Income"]),
            },
            "providers": ["Vanguard", "BlackRock", "Betashares", "State Street", "ETFS"],
            "all_tickers": all_etfs
        }
    
    def get_recommended_portfolio(self, risk_profile: str = "moderate") -> List[Dict[str, Any]]:
        """Get recommended ETF portfolio based on risk profile"""
        if risk_profile.lower() == "conservative":
            etfs = ["VAF.AX", "VGB.AX", "VAS.AX", "VHY.AX"]
            weights = [0.40, 0.30, 0.20, 0.10]
        elif risk_profile.lower() == "moderate":
            etfs = ["VAS.AX", "VGS.AX", "VAF.AX", "VAP.AX"]
            weights = [0.35, 0.35, 0.20, 0.10]
        elif risk_profile.lower() == "aggressive":
            etfs = ["VGS.AX", "VAS.AX", "NDQ.AX", "VSO.AX"]
            weights = [0.40, 0.30, 0.20, 0.10]
        else:
            raise ValueError("Risk profile must be: conservative, moderate, or aggressive")
        
        portfolio = []
        for ticker, weight in zip(etfs, weights):
            info = self.universe.get_etf_info(ticker)
            portfolio.append({
                "ticker": ticker,
                "name": info["name"],
                "category": info["category"],
                "weight": weight,
                "weight_percent": weight * 100
            })
        
        return portfolio

# Global instance
ultrawealth_service = UltraWealthFinancialService()
