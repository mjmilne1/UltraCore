"""
AI-Powered Portfolio Optimizer
Modern Portfolio Theory with goal-based optimization
"""

import numpy as np
from scipy.optimize import minimize
from decimal import Decimal
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime
import logging

from ..models import (
    ETF, OptimizationConstraints, RiskMetrics,
    AssetClass, BUSINESS_RULES
)

logger = logging.getLogger(__name__)


class PortfolioOptimizer:
    """
    AI-powered portfolio optimizer using Modern Portfolio Theory
    Optimizes for Sharpe ratio with goal-based constraints
    """
    
    def __init__(self):
        self.risk_free_rate = Decimal("0.04")  # 4% risk-free rate (Australian bonds)
    
    def optimize_for_goal(
        self,
        etf_universe: List[ETF],
        target_return: Decimal,
        risk_tolerance: int,
        constraints: OptimizationConstraints,
        current_allocation: Optional[Dict[str, Decimal]] = None
    ) -> Dict:
        """
        Optimize portfolio for specific goal
        
        Returns optimal 6-ETF portfolio maximizing Sharpe ratio
        """
        logger.info(f"Starting optimization: target_return={target_return}, risk_tolerance={risk_tolerance}")
        
        # Filter eligible ETFs
        eligible_etfs = [etf for etf in etf_universe if etf.is_eligible]
        
        if len(eligible_etfs) < constraints.max_etfs:
            raise ValueError(f"Insufficient eligible ETFs: {len(eligible_etfs)} < {constraints.max_etfs}")
        
        # Calculate expected returns and covariance matrix
        returns = np.array([float(etf.returns_3y or 8.0) for etf in eligible_etfs])
        volatilities = np.array([float(etf.volatility or 15.0) for etf in eligible_etfs])
        
        # Build correlation matrix (simplified - in production use historical data)
        n = len(eligible_etfs)
        correlation_matrix = self._build_correlation_matrix(eligible_etfs)
        
        # Covariance matrix
        cov_matrix = np.outer(volatilities, volatilities) * correlation_matrix
        
        # Risk tolerance adjustment
        target_return_adjusted = self._adjust_target_for_risk_tolerance(
            target_return, risk_tolerance
        )
        
        # Run optimization
        optimal_weights = self._optimize_sharpe_ratio(
            returns, cov_matrix, target_return_adjusted, constraints
        )
        
        # Select top 6 ETFs
        top_indices = np.argsort(optimal_weights)[-constraints.max_etfs:]
        selected_etfs = [eligible_etfs[i] for i in top_indices]
        selected_weights = optimal_weights[top_indices]
        
        # Normalize weights to sum to 100%
        selected_weights = selected_weights / selected_weights.sum() * 100
        
        # Build allocation
        allocation = []
        for etf, weight in zip(selected_etfs, selected_weights):
            allocation.append({
                "etf_code": etf.etf_code,
                "etf_name": etf.etf_name,
                "weight": Decimal(str(round(weight, 2))),
                "asset_class": etf.asset_class.value,
                "expense_ratio": etf.expense_ratio,
                "franking_yield": etf.franking_yield,
                "expected_return": etf.returns_3y or Decimal("8.0"),
                "volatility": etf.volatility or Decimal("15.0")
            })
        
        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(
            allocation, cov_matrix, top_indices
        )
        
        logger.info(f"Optimization complete: {len(allocation)} ETFs selected, Sharpe={portfolio_metrics['sharpe_ratio']}")
        
        return {
            "allocation": allocation,
            "metrics": portfolio_metrics,
            "optimization_date": datetime.utcnow().isoformat()
        }
    
    def _build_correlation_matrix(self, etfs: List[ETF]) -> np.ndarray:
        """Build correlation matrix for ETFs"""
        n = len(etfs)
        corr_matrix = np.eye(n)
        
        # Simplified correlation model
        # In production, use historical price data
        for i in range(n):
            for j in range(i+1, n):
                etf_i = etfs[i]
                etf_j = etfs[j]
                
                # Same asset class: high correlation
                if etf_i.asset_class == etf_j.asset_class:
                    corr = 0.85
                # Equity classes: moderate correlation
                elif (etf_i.asset_class in [AssetClass.AUSTRALIAN_EQUITY, AssetClass.INTERNATIONAL_EQUITY] and
                      etf_j.asset_class in [AssetClass.AUSTRALIAN_EQUITY, AssetClass.INTERNATIONAL_EQUITY]):
                    corr = 0.65
                # Equity vs bonds: low/negative correlation
                elif (etf_i.asset_class in [AssetClass.AUSTRALIAN_EQUITY, AssetClass.INTERNATIONAL_EQUITY] and
                      etf_j.asset_class == AssetClass.FIXED_INCOME):
                    corr = 0.15
                # Default: low correlation
                else:
                    corr = 0.30
                
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr
        
        return corr_matrix
    
    def _adjust_target_for_risk_tolerance(
        self,
        target_return: Decimal,
        risk_tolerance: int
    ) -> float:
        """Adjust target return based on risk tolerance (1-10 scale)"""
        # Risk tolerance 1 (very conservative) -> lower target
        # Risk tolerance 10 (very aggressive) -> higher target
        adjustment_factor = 0.7 + (risk_tolerance - 1) * 0.05  # 0.7 to 1.15
        return float(target_return) * adjustment_factor
    
    def _optimize_sharpe_ratio(
        self,
        returns: np.ndarray,
        cov_matrix: np.ndarray,
        target_return: float,
        constraints: OptimizationConstraints
    ) -> np.ndarray:
        """
        Optimize portfolio to maximize Sharpe ratio
        Subject to constraints
        """
        n_assets = len(returns)
        
        # Objective: Negative Sharpe ratio (minimize)
        def objective(weights):
            portfolio_return = np.dot(weights, returns)
            portfolio_std = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            sharpe = (portfolio_return - float(self.risk_free_rate)) / portfolio_std
            return -sharpe  # Minimize negative = maximize positive
        
        # Constraints
        constraints_list = [
            # Weights sum to 1
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
        ]
        
        # Bounds: each weight between min and max
        min_weight = float(constraints.min_weight_per_etf) / 100.0
        max_weight = float(constraints.max_weight_per_etf) / 100.0
        bounds = tuple((0.0, max_weight) for _ in range(n_assets))
        
        # Initial guess: equal weights
        initial_weights = np.array([1.0 / n_assets] * n_assets)
        
        # Optimize
        result = minimize(
            objective,
            initial_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")
        
        return result.x
    
    def _calculate_portfolio_metrics(
        self,
        allocation: List[Dict],
        cov_matrix: np.ndarray,
        selected_indices: np.ndarray
    ) -> Dict:
        """Calculate portfolio metrics"""
        weights = np.array([float(a["weight"]) / 100.0 for a in allocation])
        returns = np.array([float(a["expected_return"]) for a in allocation])
        
        # Extract covariance submatrix for selected ETFs
        cov_sub = cov_matrix[np.ix_(selected_indices, selected_indices)]
        
        # Portfolio return
        portfolio_return = np.dot(weights, returns)
        
        # Portfolio volatility
        portfolio_variance = np.dot(weights, np.dot(cov_sub, weights))
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Sharpe ratio
        sharpe_ratio = (portfolio_return - float(self.risk_free_rate)) / portfolio_volatility
        
        # Max drawdown (estimated from volatility)
        max_drawdown = portfolio_volatility * 2.0  # Simplified estimate
        
        # Total expense ratio
        total_expense_ratio = sum(
            float(a["weight"]) / 100.0 * float(a["expense_ratio"])
            for a in allocation
        )
        
        # Franking yield
        franking_yield = sum(
            float(a["weight"]) / 100.0 * float(a["franking_yield"])
            for a in allocation
        )
        
        return {
            "expected_return": Decimal(str(round(portfolio_return, 2))),
            "expected_volatility": Decimal(str(round(portfolio_volatility, 2))),
            "sharpe_ratio": Decimal(str(round(sharpe_ratio, 3))),
            "max_drawdown": Decimal(str(round(max_drawdown, 2))),
            "total_expense_ratio": Decimal(str(round(total_expense_ratio, 3))),
            "franking_yield": Decimal(str(round(franking_yield, 2)))
        }
    
    def calculate_required_return(
        self,
        current_value: Decimal,
        target_value: Decimal,
        monthly_contribution: Decimal,
        months_to_goal: int
    ) -> Decimal:
        """
        Calculate required annual return to reach goal
        Using future value of annuity formula
        """
        if months_to_goal <= 0:
            return Decimal("0")
        
        # FV = PV * (1 + r)^n + PMT * ((1 + r)^n - 1) / r
        # Solve for r using Newton's method
        
        target = float(target_value)
        pv = float(current_value)
        pmt = float(monthly_contribution)
        n = months_to_goal
        
        # Initial guess: 8% annual = 0.67% monthly
        r = 0.0067
        
        for _ in range(100):  # Max iterations
            fv = pv * (1 + r) ** n + pmt * ((1 + r) ** n - 1) / r
            
            if abs(fv - target) < 0.01:
                break
            
            # Derivative
            dfv = (
                pv * n * (1 + r) ** (n - 1) +
                pmt * (n * (1 + r) ** (n - 1) / r - ((1 + r) ** n - 1) / r ** 2)
            )
            
            # Newton's method update
            r = r - (fv - target) / dfv
        
        # Convert monthly to annual
        annual_return = (1 + r) ** 12 - 1
        return Decimal(str(round(annual_return * 100, 2)))
    
    def optimize_for_glide_path(
        self,
        etf_universe: List[ETF],
        target_equity_weight: Decimal,
        target_defensive_weight: Decimal,
        constraints: OptimizationConstraints
    ) -> Dict:
        """
        Optimize portfolio for glide path transition
        Maintains target equity/defensive allocation
        """
        logger.info(f"Glide path optimization: equity={target_equity_weight}%, defensive={target_defensive_weight}%")
        
        # Filter ETFs by asset class
        equity_etfs = [
            etf for etf in etf_universe
            if etf.is_eligible and etf.asset_class in [
                AssetClass.AUSTRALIAN_EQUITY,
                AssetClass.INTERNATIONAL_EQUITY
            ]
        ]
        
        defensive_etfs = [
            etf for etf in etf_universe
            if etf.is_eligible and etf.asset_class in [
                AssetClass.FIXED_INCOME,
                AssetClass.CASH
            ]
        ]
        
        # Select best ETFs from each class
        equity_allocation = self._select_best_etfs(
            equity_etfs,
            target_weight=target_equity_weight,
            max_etfs=4  # Max 4 equity ETFs
        )
        
        defensive_allocation = self._select_best_etfs(
            defensive_etfs,
            target_weight=target_defensive_weight,
            max_etfs=2  # Max 2 defensive ETFs
        )
        
        # Combine allocations
        allocation = equity_allocation + defensive_allocation
        
        # Calculate metrics
        portfolio_metrics = self._calculate_combined_metrics(allocation)
        
        return {
            "allocation": allocation,
            "metrics": portfolio_metrics,
            "optimization_date": datetime.utcnow().isoformat()
        }
    
    def _select_best_etfs(
        self,
        etfs: List[ETF],
        target_weight: Decimal,
        max_etfs: int
    ) -> List[Dict]:
        """Select best ETFs from a category"""
        # Sort by Sharpe ratio (or returns if Sharpe not available)
        sorted_etfs = sorted(
            etfs,
            key=lambda e: float(e.sharpe_ratio or e.returns_3y or 0),
            reverse=True
        )
        
        # Select top N
        selected = sorted_etfs[:max_etfs]
        
        # Equal weight within category
        weight_per_etf = target_weight / len(selected)
        
        allocation = []
        for etf in selected:
            allocation.append({
                "etf_code": etf.etf_code,
                "etf_name": etf.etf_name,
                "weight": weight_per_etf,
                "asset_class": etf.asset_class.value,
                "expense_ratio": etf.expense_ratio,
                "franking_yield": etf.franking_yield,
                "expected_return": etf.returns_3y or Decimal("8.0"),
                "volatility": etf.volatility or Decimal("15.0")
            })
        
        return allocation
    
    def _calculate_combined_metrics(self, allocation: List[Dict]) -> Dict:
        """Calculate metrics for combined allocation"""
        # Weighted average return
        expected_return = sum(
            float(a["weight"]) / 100.0 * float(a["expected_return"])
            for a in allocation
        )
        
        # Weighted average volatility (simplified)
        expected_volatility = sum(
            float(a["weight"]) / 100.0 * float(a["volatility"])
            for a in allocation
        )
        
        # Sharpe ratio
        sharpe_ratio = (expected_return - float(self.risk_free_rate)) / expected_volatility
        
        # Total expense ratio
        total_expense_ratio = sum(
            float(a["weight"]) / 100.0 * float(a["expense_ratio"])
            for a in allocation
        )
        
        # Franking yield
        franking_yield = sum(
            float(a["weight"]) / 100.0 * float(a["franking_yield"])
            for a in allocation
        )
        
        return {
            "expected_return": Decimal(str(round(expected_return, 2))),
            "expected_volatility": Decimal(str(round(expected_volatility, 2))),
            "sharpe_ratio": Decimal(str(round(sharpe_ratio, 3))),
            "max_drawdown": Decimal(str(round(expected_volatility * 2.0, 2))),
            "total_expense_ratio": Decimal(str(round(total_expense_ratio, 3))),
            "franking_yield": Decimal(str(round(franking_yield, 2)))
        }
