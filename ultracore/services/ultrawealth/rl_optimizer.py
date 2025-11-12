"""
UltraOptimiser Integration for UltraWealth
Uses existing optimizer from src/ultracore/ml/optimiser_models.py
"""

import sys
import os
from typing import Dict, List
import pandas as pd
import numpy as np

# Add src to path
SRC_PATH = os.path.join(os.path.dirname(__file__), '../../../src')
if os.path.exists(SRC_PATH):
    sys.path.insert(0, os.path.abspath(SRC_PATH))

class UltraOptimiserIntegration:
    """Integration wrapper for UltraOptimiser"""
    
    def __init__(self):
        self.optimiser = None
        self._load_optimiser()
    
    def _load_optimiser(self):
        """Load UltraOptimiser from src/ultracore/ml/optimiser_models.py"""
        try:
            from ultracore.ml.optimiser_models import PortfolioOptimiser
            self.optimiser = PortfolioOptimiser()
            print("✅ UltraOptimiser loaded from src/ultracore/ml/optimiser_models.py")
        except ImportError as e:
            print(f"⚠️  Could not load UltraOptimiser: {e}")
            print("   Using fallback optimizer")
            self.optimiser = None
        except Exception as e:
            print(f"⚠️  Error loading UltraOptimiser: {e}")
            self.optimiser = None
    
    async def optimize_portfolio(
        self,
        etf_data: Dict[str, pd.DataFrame],
        initial_balance: float = 100000,
        risk_tolerance: str = "moderate"
    ) -> Dict:
        """Optimize portfolio using UltraOptimiser or fallback"""
        
        if self.optimiser:
            return await self._optimize_with_ultraoptimiser(
                etf_data, initial_balance, risk_tolerance
            )
        else:
            return await self._optimize_fallback(
                etf_data, initial_balance, risk_tolerance
            )
    
    async def _optimize_with_ultraoptimiser(
        self,
        etf_data: Dict[str, pd.DataFrame],
        initial_balance: float,
        risk_tolerance: str
    ) -> Dict:
        """Optimize using UltraOptimiser from optimiser_models.py"""
        
        # Prepare returns data
        returns_data = {}
        prices_data = {}
        
        for ticker, df in etf_data.items():
            returns_data[ticker] = df['Close'].pct_change().dropna()
            prices_data[ticker] = df['Close']
        
        returns_df = pd.DataFrame(returns_data)
        prices_df = pd.DataFrame(prices_data)
        
        # Map risk tolerance
        risk_params = {
            "conservative": {"risk_level": "low", "target_return": 0.05},
            "moderate": {"risk_level": "medium", "target_return": 0.08},
            "aggressive": {"risk_level": "high", "target_return": 0.12}
        }
        
        params = risk_params.get(risk_tolerance, risk_params["moderate"])
        
        try:
            # Call UltraOptimiser
            # Adjust based on actual UltraOptimiser API
            result = self.optimiser.optimize(
                returns=returns_df,
                prices=prices_df,
                initial_capital=initial_balance,
                **params
            )
            
            # Format for UltraWealth
            allocation = {}
            weights = result.get('weights', result.get('allocation', {}))
            
            for ticker, weight in weights.items():
                allocation[ticker] = {
                    'weight': float(weight),
                    'weight_pct': float(weight * 100),
                    'amount': float(initial_balance * weight)
                }
            
            return {
                'allocation': allocation,
                'portfolio_metrics': {
                    'expected_return_annual': float(result.get('expected_return', 0) * 100),
                    'volatility_annual': float(result.get('volatility', result.get('risk', 0)) * 100),
                    'sharpe_ratio': float(result.get('sharpe_ratio', 0))
                },
                'risk_tolerance': risk_tolerance,
                'optimizer': 'UltraOptimiser',
                'method': result.get('method', 'reinforcement_learning')
            }
            
        except Exception as e:
            print(f"⚠️  UltraOptimiser error: {e}")
            print("   Falling back to mean-variance optimization")
            return await self._optimize_fallback(etf_data, initial_balance, risk_tolerance)
    
    async def _optimize_fallback(
        self,
        etf_data: Dict[str, pd.DataFrame],
        initial_balance: float,
        risk_tolerance: str
    ) -> Dict:
        """Fallback: Mean-variance optimization"""
        
        returns_data = {}
        for ticker, df in etf_data.items():
            returns_data[ticker] = df['Close'].pct_change().dropna()
        
        returns_df = pd.DataFrame(returns_data)
        mean_returns = returns_df.mean()
        cov_matrix = returns_df.cov()
        std_devs = returns_df.std()
        
        # Calculate Sharpe ratios
        sharpe_ratios = mean_returns / std_devs
        sharpe_ratios = sharpe_ratios.fillna(0)
        
        # Optimize weights based on Sharpe
        weights = sharpe_ratios / sharpe_ratios.sum()
        weights = np.maximum(weights.values, 0)
        weights = weights / weights.sum()
        
        # Apply risk tolerance adjustments
        if risk_tolerance == "conservative":
            # Lower concentration, more diversification
            weights = weights * 0.7  # 30% cash buffer
        elif risk_tolerance == "aggressive":
            # Concentrate in top performers
            n_assets = len(weights)
            top_n = max(2, n_assets // 2)
            top_indices = np.argsort(sharpe_ratios)[-top_n:]
            adjusted = np.zeros_like(weights)
            adjusted[top_indices] = weights[top_indices]
            weights = adjusted / adjusted.sum() if adjusted.sum() > 0 else weights
        
        weights = weights / weights.sum()  # Renormalize
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(weights, mean_returns) * 252
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
        sharpe = portfolio_return / portfolio_std if portfolio_std > 0 else 0
        
        allocation = {}
        tickers = list(etf_data.keys())
        for i, ticker in enumerate(tickers):
            allocation[ticker] = {
                'weight': float(weights[i]),
                'weight_pct': float(weights[i] * 100),
                'amount': float(initial_balance * weights[i])
            }
        
        return {
            'allocation': allocation,
            'portfolio_metrics': {
                'expected_return_annual': float(portfolio_return * 100),
                'volatility_annual': float(portfolio_std * 100),
                'sharpe_ratio': float(sharpe)
            },
            'risk_tolerance': risk_tolerance,
            'optimizer': 'Mean-Variance (Fallback)',
            'method': 'sharpe_ratio_optimization'
        }

# Create global instance
rl_optimizer = UltraOptimiserIntegration()
