"""UltraOptimiser Integration - Portfolio Optimization"""
from typing import Dict, List
from decimal import Decimal
import numpy as np

from ultracore.domains.ultraoptimiser.services import OptimisationService


class UltraOptimiserAdapter:
    """
    Adapter for UltraOptimiser integration.
    
    UltraOptimiser Achievements (Existing):
    - Expected return: 8.89% p.a.
    - Sharpe ratio: 0.66
    - Maximum drawdown: -15.23%
    - Win rate: 62.5%
    
    Integration:
    - Portfolio construction
    - Asset allocation optimization
    - Risk-adjusted returns
    - Rebalancing recommendations
    """
    
    def __init__(self, optimiser: OptimisationService):
        self.optimiser = optimiser
    
    async def optimize_portfolio(
        self,
        risk_tolerance: str,
        time_horizon_years: int,
        current_holdings: Dict[str, Decimal],
        available_cash: Decimal,
        constraints: Dict = None
    ) -> Dict:
        """
        Optimize portfolio using UltraOptimiser.
        
        Returns target allocation with expected returns and risk.
        """
        
        # Map risk tolerance to UltraOptimiser risk level
        risk_mapping = {
            "low": 0.3,      # Conservative: 30% risk budget
            "medium": 0.6,   # Balanced: 60% risk budget
            "high": 0.9      # Growth: 90% risk budget
        }
        
        risk_budget = risk_mapping.get(risk_tolerance, 0.6)
        
        # Build universe of securities
        universe = self._build_universe(risk_tolerance, time_horizon_years)
        
        # Run optimization
        result = await self.optimiser.optimize(
            universe=universe,
            risk_budget=risk_budget,
            current_holdings=current_holdings,
            available_cash=float(available_cash),
            constraints=constraints or {}
        )
        
        return {
            "target_allocation": result["optimal_weights"],
            "expected_return": result["expected_return"],
            "expected_volatility": result["volatility"],
            "sharpe_ratio": result["sharpe_ratio"],
            "recommended_trades": result["rebalancing_trades"],
            "optimization_score": result["optimization_score"]
        }
    
    def _build_universe(
        self,
        risk_tolerance: str,
        time_horizon_years: int
    ) -> List[str]:
        """
        Build investment universe based on risk profile.
        
        Australian Securities:
        - Conservative: Cash, bonds, defensive stocks
        - Balanced: Mix of growth and defensive
        - Growth: Growth stocks, international exposure
        """
        
        # Core Australian ETFs (actual ASX codes)
        universe = []
        
        if risk_tolerance in ["low", "medium"]:
            # Conservative/Defensive
            universe.extend([
                "VAS",   # Vanguard Australian Shares
                "VGB",   # Vanguard Australian Government Bonds
                "VAF",   # Vanguard Australian Fixed Interest
                "VHY",   # Vanguard Australian Shares High Yield
            ])
        
        if risk_tolerance in ["medium", "high"]:
            # Balanced/Growth
            universe.extend([
                "VGS",   # Vanguard MSCI International Shares
                "VGE",   # Vanguard FTSE Emerging Markets
                "VDHG",  # Vanguard Diversified High Growth
                "IOZ",   # iShares Core S&P/ASX 200
            ])
        
        if risk_tolerance == "high":
            # Aggressive/Growth
            universe.extend([
                "NDQ",   # BetaShares NASDAQ 100
                "ASIA",  # BetaShares Asia Technology Tigers
                "HACK",  # BetaShares Global Cybersecurity
            ])
        
        return universe
    
    async def check_rebalancing_needed(
        self,
        current_allocation: Dict[str, Decimal],
        target_allocation: Dict[str, Decimal],
        threshold: Decimal = Decimal("0.05")
    ) -> Dict:
        """
        Check if portfolio needs rebalancing.
        
        Triggers rebalancing if allocation drift > threshold.
        """
        
        needs_rebalancing = False
        drift_details = {}
        
        for asset, target_weight in target_allocation.items():
            current_weight = current_allocation.get(asset, Decimal("0"))
            drift = abs(current_weight - target_weight)
            
            drift_details[asset] = {
                "current": float(current_weight),
                "target": float(target_weight),
                "drift": float(drift)
            }
            
            if drift > threshold:
                needs_rebalancing = True
        
        return {
            "needs_rebalancing": needs_rebalancing,
            "threshold": float(threshold),
            "drift_details": drift_details,
            "recommendation": "Rebalance recommended" if needs_rebalancing else "Portfolio within tolerance"
        }
