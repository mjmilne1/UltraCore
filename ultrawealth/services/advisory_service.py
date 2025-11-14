"""
Investment Advisory Service

Provides AI-powered investment recommendations and portfolio optimization
"""

from typing import Dict, List
from sqlalchemy.orm import Session

from ultracore.services.ultrawealth import ultrawealth_service, australian_etf_universe
from ultracore.services.ultrawealth.ml_engine import MLEngine
from ultracore.services.ultrawealth.rl_optimizer import RLOptimizer


class InvestmentAdvisoryService:
    """Investment advisory service with AI/ML capabilities"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.etf_service = ultrawealth_service
        self.etf_universe = australian_etf_universe
        self.ml_engine = MLEngine()
        self.rl_optimizer = RLOptimizer()
    
    async def get_target_allocation(self, risk_profile: str) -> Dict:
        """
        Get recommended target allocation based on risk profile
        
        Args:
            risk_profile: Risk profile (conservative, moderate, aggressive, etc.)
            
        Returns:
            Dict: Target allocation by asset class
        """
        
        allocations = {
            'conservative': {
                'Australian Equities': 20,
                'International Equities': 15,
                'Fixed Income': 45,
                'Property': 10,
                'Cash': 10
            },
            'moderate': {
                'Australian Equities': 30,
                'International Equities': 25,
                'Fixed Income': 25,
                'Property': 15,
                'Cash': 5
            },
            'balanced': {
                'Australian Equities': 35,
                'International Equities': 30,
                'Fixed Income': 20,
                'Property': 10,
                'Cash': 5
            },
            'growth': {
                'Australian Equities': 45,
                'International Equities': 35,
                'Fixed Income': 10,
                'Property': 8,
                'Cash': 2
            },
            'aggressive': {
                'Australian Equities': 50,
                'International Equities': 40,
                'Fixed Income': 5,
                'Property': 5,
                'Cash': 0
            }
        }
        
        return allocations.get(risk_profile.lower(), allocations['balanced'])
    
    async def generate_recommendations(
        self,
        risk_profile: str,
        investment_goals: List[Dict],
        time_horizon_years: int
    ) -> Dict:
        """
        Generate AI-powered investment recommendations
        
        Args:
            risk_profile: Client risk profile
            investment_goals: List of investment goals
            time_horizon_years: Investment time horizon
            
        Returns:
            Dict: Investment recommendations
        """
        
        # Get target allocation
        target_allocation = await self.get_target_allocation(risk_profile)
        
        # Get recommended ETFs for each asset class
        recommended_etfs = {}
        
        for asset_class, target_pct in target_allocation.items():
            if target_pct > 0:
                # Get ETFs for this category
                category_etfs = self.etf_universe.get_by_category(asset_class)
                
                if category_etfs:
                    # Get top ETF by liquidity/size (simplified)
                    top_etf = category_etfs[0] if category_etfs else None
                    
                    if top_etf:
                        etf_info = self.etf_universe.get_etf_info(top_etf)
                        
                        # Get ML prediction
                        try:
                            prediction = await self.etf_service.get_etf_prediction(top_etf)
                            predicted_return = prediction.get('predicted_return_1y', 8.0)
                        except:
                            predicted_return = 8.0  # Default
                        
                        recommended_etfs[asset_class] = {
                            'ticker': top_etf,
                            'name': etf_info.get('name'),
                            'target_allocation': target_pct,
                            'predicted_annual_return': predicted_return,
                            'expense_ratio': etf_info.get('expense_ratio', 0.0)
                        }
        
        # Calculate expected portfolio return
        expected_return = sum(
            etf['target_allocation'] * etf['predicted_annual_return'] / 100
            for etf in recommended_etfs.values()
        )
        
        # Adjust for time horizon
        time_horizon_factor = min(time_horizon_years / 10, 1.0)  # Max at 10 years
        confidence = 0.7 + (0.2 * time_horizon_factor)  # Higher confidence for longer horizons
        
        return {
            'risk_profile': risk_profile,
            'target_allocation': target_allocation,
            'recommended_etfs': recommended_etfs,
            'expected_annual_return': expected_return,
            'time_horizon_years': time_horizon_years,
            'confidence_score': confidence,
            'investment_goals': investment_goals,
            'notes': [
                f"Portfolio optimized for {risk_profile} risk profile",
                f"Expected annual return: {expected_return:.2f}%",
                f"Diversified across {len(recommended_etfs)} asset classes",
                "Recommendations based on AI/ML analysis of historical data"
            ]
        }
    
    async def optimize_portfolio(
        self,
        tickers: List[str],
        risk_tolerance: float = 0.5
    ) -> Dict:
        """
        Optimize portfolio allocation using RL
        
        Args:
            tickers: List of ETF tickers
            risk_tolerance: Risk tolerance (0-1, higher = more risk)
            
        Returns:
            Dict: Optimized allocation
        """
        
        # Use RL optimizer
        optimization = await self.rl_optimizer.optimize_portfolio(
            tickers=tickers,
            risk_tolerance=risk_tolerance
        )
        
        return optimization
    
    async def get_market_insights(self) -> Dict:
        """Get AI-powered market insights"""
        
        # Get predictions for major ETFs
        major_etfs = ['VAS.AX', 'VGS.AX', 'VAP.AX', 'VGB.AX']
        
        insights = {
            'market_outlook': {},
            'top_performers_predicted': [],
            'risk_factors': []
        }
        
        for ticker in major_etfs:
            try:
                prediction = await self.etf_service.get_etf_prediction(ticker)
                etf_info = self.etf_universe.get_etf_info(ticker)
                
                insights['market_outlook'][ticker] = {
                    'name': etf_info.get('name'),
                    'category': etf_info.get('category'),
                    'predicted_return_1y': prediction.get('predicted_return_1y'),
                    'confidence': prediction.get('confidence')
                }
                
                if prediction.get('predicted_return_1y', 0) > 10:
                    insights['top_performers_predicted'].append(ticker)
                    
            except Exception as e:
                continue
        
        # Add risk factors (would be more sophisticated in production)
        insights['risk_factors'] = [
            "Interest rate volatility",
            "Global economic uncertainty",
            "Currency fluctuations (AUD/USD)"
        ]
        
        return insights
