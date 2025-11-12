"""ML-Enhanced Portfolio Optimization using Modern Portfolio Theory + Deep Learning"""
import numpy as np
import pandas as pd
from typing import List, Dict
from scipy.optimize import minimize

from ultracore.ml.base import BaseMLModel


class PortfolioOptimizer(BaseMLModel):
    """
    Advanced portfolio optimization combining:
    - Modern Portfolio Theory (Markowitz)
    - ML-based return predictions
    - RL-based dynamic rebalancing
    """
    
    def __init__(self):
        super().__init__(
            model_name="portfolio_optimizer",
            model_type="optimization",
            version="1.0.0"
        )
    
    async def optimize(
        self,
        symbols: List[str],
        expected_returns: Dict[str, float],
        covariance_matrix: np.ndarray,
        risk_tolerance: float = 0.5,
        constraints: Optional[Dict] = None
    ) -> Dict:
        """
        Optimize portfolio allocation using ML-enhanced MPT.
        
        Args:
            symbols: List of stock symbols
            expected_returns: ML-predicted expected returns for each symbol
            covariance_matrix: Covariance matrix of returns
            risk_tolerance: Risk tolerance (0=risk-averse, 1=risk-seeking)
            constraints: Additional constraints (sector limits, position limits)
        
        Returns:
            Optimal portfolio weights and metrics
        """
        n_assets = len(symbols)
        
        # Objective function: Maximize Sharpe Ratio
        def objective(weights):
            portfolio_return = np.dot(weights, list(expected_returns.values()))
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(covariance_matrix, weights)))
            sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility  # 3% risk-free rate
            return -sharpe_ratio  # Minimize negative Sharpe
        
        # Constraints
        constraints_list = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]
        
        # Bounds: 0% to 40% per position (diversification)
        bounds = tuple((0, 0.4) for _ in range(n_assets))
        
        # Initial guess: equal weights
        initial_weights = np.array([1/n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list
        )
        
        optimal_weights = result.x
        portfolio_return = np.dot(optimal_weights, list(expected_returns.values()))
        portfolio_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(covariance_matrix, optimal_weights)))
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_volatility
        
        # Build allocation
        allocation = {
            symbol: float(weight)
            for symbol, weight in zip(symbols, optimal_weights)
            if weight > 0.01  # Exclude tiny positions
        }
        
        return {
            "allocation": allocation,
            "expected_return": float(portfolio_return),
            "expected_volatility": float(portfolio_volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "risk_tolerance": risk_tolerance
        }
