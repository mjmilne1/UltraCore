"""
Portfolio Analyzer
Advanced portfolio analytics using Fiscal.ai data
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics
from loguru import logger
from .service import FiscalAIService


class PortfolioAnalyzer:
    """Advanced portfolio analysis and insights"""
    
    def __init__(self, fiscal_service: Optional[FiscalAIService] = None):
        self.fiscal_service = fiscal_service or FiscalAIService()
    
    async def analyze_portfolio_health(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Comprehensive portfolio health analysis
        
        Args:
            holdings: Portfolio holdings
            
        Returns:
            Health score and analysis
        """
        enriched = await self.fiscal_service.get_portfolio_holdings_data(holdings)
        
        # Extract key metrics
        pe_ratios = []
        debt_to_equity = []
        roe_values = []
        revenue_growth = []
        
        for holding in enriched:
            fiscal_data = holding.get("fiscal_data", {})
            ratios = fiscal_data.get("ratios", {})
            
            if ratios:
                if ratios.get("peRatio"):
                    pe_ratios.append(ratios["peRatio"])
                if ratios.get("debtToEquity"):
                    debt_to_equity.append(ratios["debtToEquity"])
                if ratios.get("returnOnEquity"):
                    roe_values.append(ratios["returnOnEquity"])
        
        # Calculate health score (0-100)
        health_score = 70  # Base score
        
        # Adjust based on metrics
        if pe_ratios:
            avg_pe = statistics.mean(pe_ratios)
            if 10 < avg_pe < 25:  # Healthy P/E range
                health_score += 10
            elif avg_pe > 40:  # Overvalued
                health_score -= 10
        
        if roe_values:
            avg_roe = statistics.mean(roe_values)
            if avg_roe > 0.15:  # Strong ROE
                health_score += 10
            elif avg_roe < 0.05:  # Weak ROE
                health_score -= 10
        
        if debt_to_equity:
            avg_debt = statistics.mean(debt_to_equity)
            if avg_debt < 0.5:  # Low debt
                health_score += 5
            elif avg_debt > 2.0:  # High debt
                health_score -= 10
        
        # Ensure score is within bounds
        health_score = max(0, min(100, health_score))
        
        return {
            "health_score": health_score,
            "metrics": {
                "average_pe_ratio": statistics.mean(pe_ratios) if pe_ratios else None,
                "average_roe": statistics.mean(roe_values) if roe_values else None,
                "average_debt_to_equity": statistics.mean(debt_to_equity) if debt_to_equity else None,
            },
            "insights": self._generate_health_insights(health_score, {
                "pe": statistics.mean(pe_ratios) if pe_ratios else None,
                "roe": statistics.mean(roe_values) if roe_values else None,
                "debt": statistics.mean(debt_to_equity) if debt_to_equity else None,
            }),
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def _generate_health_insights(
        self,
        score: float,
        metrics: Dict[str, Optional[float]]
    ) -> List[str]:
        """Generate human-readable insights"""
        insights = []
        
        if score >= 80:
            insights.append("Portfolio shows strong financial health")
        elif score >= 60:
            insights.append("Portfolio health is moderate")
        else:
            insights.append("Portfolio may need rebalancing")
        
        if metrics.get("pe") and metrics["pe"] > 35:
            insights.append("Holdings may be overvalued based on P/E ratios")
        
        if metrics.get("roe") and metrics["roe"] > 0.20:
            insights.append("Strong return on equity across holdings")
        
        if metrics.get("debt") and metrics["debt"] > 1.5:
            insights.append("Holdings have elevated debt levels")
        
        return insights
    
    async def get_diversification_analysis(
        self,
        holdings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze portfolio diversification
        
        Args:
            holdings: Portfolio holdings
            
        Returns:
            Diversification metrics and recommendations
        """
        enriched = await self.fiscal_service.get_portfolio_holdings_data(holdings)
        
        sectors = {}
        industries = {}
        
        for holding in enriched:
            fiscal_data = holding.get("fiscal_data", {})
            profile = fiscal_data.get("profile", {})
            
            sector = profile.get("sector", "Unknown")
            industry = profile.get("industry", "Unknown")
            
            quantity = holding.get("quantity", 0)
            price = fiscal_data.get("current_price", 0)
            value = quantity * price
            
            sectors[sector] = sectors.get(sector, 0) + value
            industries[industry] = industries.get(industry, 0) + value
        
        total_value = sum(sectors.values())
        
        # Calculate concentration
        max_sector_pct = (max(sectors.values()) / total_value * 100) if total_value > 0 else 0
        
        diversification_score = 100
        if max_sector_pct > 50:
            diversification_score -= 30
        elif max_sector_pct > 30:
            diversification_score -= 15
        
        if len(sectors) < 3:
            diversification_score -= 20
        
        return {
            "diversification_score": max(0, min(100, diversification_score)),
            "sector_breakdown": {
                sector: {
                    "value": value,
                    "percentage": (value / total_value * 100) if total_value > 0 else 0
                }
                for sector, value in sectors.items()
            },
            "industry_breakdown": {
                industry: {
                    "value": value,
                    "percentage": (value / total_value * 100) if total_value > 0 else 0
                }
                for industry, value in industries.items()
            },
            "sectors_count": len(sectors),
            "industries_count": len(industries),
            "max_sector_concentration": max_sector_pct,
            "recommendations": self._generate_diversification_recommendations(
                diversification_score,
                max_sector_pct,
                len(sectors)
            )
        }
    
    def _generate_diversification_recommendations(
        self,
        score: float,
        max_concentration: float,
        sector_count: int
    ) -> List[str]:
        """Generate diversification recommendations"""
        recommendations = []
        
        if score < 60:
            recommendations.append("Consider diversifying across more sectors")
        
        if max_concentration > 40:
            recommendations.append(
                f"Reduce concentration in dominant sector ({max_concentration:.1f}%)"
            )
        
        if sector_count < 4:
            recommendations.append("Add holdings from underrepresented sectors")
        
        if not recommendations:
            recommendations.append("Portfolio shows healthy diversification")
        
        return recommendations
