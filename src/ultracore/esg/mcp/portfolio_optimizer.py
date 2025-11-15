"""
ESG Portfolio Optimizer

This module implements the full RL-powered portfolio optimization using the Epsilon Agent.
It converts portfolio holdings into state representations, runs the agent to generate
optimal actions, and produces detailed optimization results.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

from ultracore.esg.agents.epsilon_agent import EpsilonAgent
from ultracore.esg.data.esg_data_loader import EsgDataLoader


class EsgPortfolioOptimizer:
    """
    RL-powered ESG portfolio optimizer using the Epsilon Agent.
    
    This class bridges the gap between human-readable portfolio representations
    and the state/action vectors required by the RL agent.
    """
    
    def __init__(
        self,
        esg_data_loader: EsgDataLoader,
        epsilon_agent: EpsilonAgent,
        asset_universe: List[str],  # List of ISINs
        lookback_days: int = 252  # 1 year of trading days
    ):
        """
        Initialize the portfolio optimizer.
        
        Args:
            esg_data_loader: Loader for ESG data
            epsilon_agent: Trained Epsilon Agent
            asset_universe: List of ISINs that can be invested in
            lookback_days: Number of days of historical data to use for state
        """
        self.esg_data_loader = esg_data_loader
        self.epsilon_agent = epsilon_agent
        self.asset_universe = asset_universe
        self.lookback_days = lookback_days
        
        # ESG rating mapping
        self.rating_map = {
            'AAA': 7, 'AA': 6, 'A': 5, 'BBB': 4, 'BB': 3, 'B': 2, 'CCC': 1
        }
        self.rating_reverse_map = {v: k for k, v in self.rating_map.items()}
    
    def optimize(
        self,
        current_portfolio: Dict[str, float],
        objectives: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize a portfolio using RL-powered ESG-aware optimization.
        
        Args:
            current_portfolio: Current holdings {ISIN: weight}
            objectives: Optimization objectives
            constraints: Optional ESG constraints
        
        Returns:
            Optimization results including new portfolio, metrics, and trade list
        """
        # Step 1: Build state representation
        state = self._build_state(current_portfolio)
        
        # Step 2: Extract ESG constraints from objectives and constraints
        esg_constraints = self._extract_constraints(objectives, constraints)
        
        # Step 3: Run Epsilon Agent to get optimal action
        action = self.epsilon_agent.select_action(
            state,
            esg_constraints=esg_constraints,
            deterministic=True
        )
        
        # Step 4: Convert action to portfolio weights
        optimized_portfolio = self._action_to_portfolio(action)
        
        # Step 5: Calculate expected metrics
        current_metrics = self._calculate_portfolio_metrics(current_portfolio)
        optimized_metrics = self._calculate_portfolio_metrics(optimized_portfolio)
        
        # Step 6: Generate trade list
        trade_list = self._generate_trade_list(current_portfolio, optimized_portfolio)
        
        # Step 7: Calculate improvement
        improvement = self._calculate_improvement(current_metrics, optimized_metrics)
        
        # Step 8: Get explanation from agent
        explanation = self.epsilon_agent.explain_action(state)
        
        return {
            "optimized_portfolio": optimized_portfolio,
            "current_metrics": current_metrics,
            "optimized_metrics": optimized_metrics,
            "improvement": improvement,
            "trade_list": trade_list,
            "explanation": explanation,
            "optimization_timestamp": datetime.now().isoformat(),
            "agent_version": "epsilon-v0.1.0"
        }
    
    def _build_state(self, portfolio: Dict[str, float]) -> np.ndarray:
        """
        Build state representation from current portfolio.
        
        State includes:
        - Historical returns (20 features per asset)
        - Current holdings (1 feature per asset)
        - ESG metrics (3 features per asset: rating, carbon, controversy)
        """
        n_assets = len(self.asset_universe)
        
        # Financial features (20 per asset)
        financial_features = []
        for isin in self.asset_universe:
            # Mock historical returns (in production, load from Data Mesh)
            returns = np.random.randn(20) * 0.01  # Daily returns
            financial_features.extend(returns)
        
        # Current holdings (1 per asset)
        holdings = []
        for isin in self.asset_universe:
            weight = portfolio.get(isin, 0.0)
            holdings.append(weight)
        
        # ESG features (3 per asset)
        esg_features = []
        for isin in self.asset_universe:
            profile = self.esg_data_loader.get_esg_profile(isin, datetime.now())
            
            if 'error' not in profile:
                # ESG rating (normalized to 0-1)
                rating = profile.get('msci_rating', 'BBB')
                rating_numeric = self.rating_map.get(rating, 4) / 7.0
                
                # Carbon intensity (normalized, capped at 500)
                carbon = profile.get('carbon_intensity', 100.0)
                carbon_normalized = min(carbon / 500.0, 1.0)
                
                # Controversy score (normalized to 0-1)
                controversy = profile.get('controversy_score', 0.0)
                controversy_normalized = controversy / 10.0
            else:
                # Default values if no ESG data
                rating_numeric = 0.5
                carbon_normalized = 0.2
                controversy_normalized = 0.0
            
            esg_features.extend([rating_numeric, carbon_normalized, controversy_normalized])
        
        # Combine all features
        state = np.concatenate([
            financial_features,
            holdings,
            esg_features
        ])
        
        return state.astype(np.float32)
    
    def _extract_constraints(
        self,
        objectives: Dict[str, Any],
        constraints: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract ESG constraints in normalized format for the agent"""
        esg_constraints = {}
        
        # From objectives
        if 'min_esg_rating' in objectives:
            rating = objectives['min_esg_rating']
            if isinstance(rating, str):
                rating_numeric = self.rating_map.get(rating, 4)
                esg_constraints['min_esg_rating'] = rating_numeric / 7.0
        
        if 'max_carbon_intensity' in objectives:
            carbon = objectives['max_carbon_intensity']
            esg_constraints['max_carbon_intensity'] = min(carbon / 500.0, 1.0)
        
        # From constraints
        if constraints:
            if 'min_esg_rating' in constraints:
                rating = constraints['min_esg_rating']
                if isinstance(rating, str):
                    rating_numeric = self.rating_map.get(rating, 4)
                    esg_constraints['min_esg_rating'] = rating_numeric / 7.0
            
            if 'max_carbon_intensity' in constraints:
                carbon = constraints['max_carbon_intensity']
                esg_constraints['max_carbon_intensity'] = min(carbon / 500.0, 1.0)
        
        return esg_constraints
    
    def _action_to_portfolio(self, action: np.ndarray) -> Dict[str, float]:
        """Convert agent action (weights) to portfolio dictionary"""
        portfolio = {}
        
        for i, isin in enumerate(self.asset_universe):
            weight = float(action[i])
            if weight > 0.01:  # Only include if weight > 1%
                portfolio[isin] = round(weight, 4)
        
        return portfolio
    
    def _calculate_portfolio_metrics(self, portfolio: Dict[str, float]) -> Dict[str, Any]:
        """Calculate comprehensive metrics for a portfolio"""
        if not portfolio:
            return {
                "total_weight": 0.0,
                "expected_return": 0.0,
                "expected_volatility": 0.0,
                "sharpe_ratio": 0.0,
                "esg_rating": "N/A",
                "carbon_intensity": 0.0,
                "board_diversity": 0.0,
                "controversy_score": 0.0
            }
        
        total_weight = sum(portfolio.values())
        
        # Financial metrics (mock - in production, calculate from historical data)
        expected_return = 0.08 + np.random.randn() * 0.02  # ~8% with noise
        expected_volatility = 0.12 + np.random.randn() * 0.02  # ~12% with noise
        sharpe_ratio = expected_return / expected_volatility if expected_volatility > 0 else 0
        
        # ESG metrics (weighted average)
        weighted_rating = 0.0
        weighted_carbon = 0.0
        weighted_diversity = 0.0
        weighted_controversy = 0.0
        
        for isin, weight in portfolio.items():
            normalized_weight = weight / total_weight if total_weight > 0 else 0
            profile = self.esg_data_loader.get_esg_profile(isin, datetime.now())
            
            if 'error' not in profile:
                rating = profile.get('msci_rating', 'BBB')
                rating_numeric = self.rating_map.get(rating, 4)
                
                weighted_rating += normalized_weight * rating_numeric
                weighted_carbon += normalized_weight * profile.get('carbon_intensity', 100.0)
                weighted_diversity += normalized_weight * profile.get('board_diversity', 30.0)
                weighted_controversy += normalized_weight * profile.get('controversy_score', 0.0)
        
        # Convert weighted rating back to letter grade
        portfolio_rating = self.rating_reverse_map.get(round(weighted_rating), 'BBB')
        
        return {
            "total_weight": round(total_weight, 4),
            "expected_return": round(expected_return, 4),
            "expected_volatility": round(expected_volatility, 4),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "esg_rating": portfolio_rating,
            "carbon_intensity": round(weighted_carbon, 2),
            "board_diversity": round(weighted_diversity, 2),
            "controversy_score": round(weighted_controversy, 2)
        }
    
    def _generate_trade_list(
        self,
        current: Dict[str, float],
        optimized: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate list of trades to move from current to optimized portfolio"""
        trades = []
        
        # Get all ISINs involved
        all_isins = set(current.keys()) | set(optimized.keys())
        
        for isin in all_isins:
            current_weight = current.get(isin, 0.0)
            optimized_weight = optimized.get(isin, 0.0)
            delta = optimized_weight - current_weight
            
            if abs(delta) > 0.01:  # Only if change > 1%
                # Get asset name
                profile = self.esg_data_loader.get_esg_profile(isin, datetime.now())
                name = profile.get('name', isin) if 'error' not in profile else isin
                
                trade = {
                    "isin": isin,
                    "name": name,
                    "action": "buy" if delta > 0 else "sell",
                    "current_weight": round(current_weight, 4),
                    "target_weight": round(optimized_weight, 4),
                    "delta": round(abs(delta), 4)
                }
                trades.append(trade)
        
        # Sort by delta (largest trades first)
        trades.sort(key=lambda x: x['delta'], reverse=True)
        
        return trades
    
    def _calculate_improvement(
        self,
        current: Dict[str, Any],
        optimized: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate improvement metrics"""
        return {
            "return_improvement": round(
                (optimized['expected_return'] - current['expected_return']) * 100, 2
            ),
            "volatility_change": round(
                (optimized['expected_volatility'] - current['expected_volatility']) * 100, 2
            ),
            "sharpe_improvement": round(
                optimized['sharpe_ratio'] - current['sharpe_ratio'], 2
            ),
            "carbon_reduction_pct": round(
                ((current['carbon_intensity'] - optimized['carbon_intensity']) / 
                 current['carbon_intensity'] * 100) if current['carbon_intensity'] > 0 else 0, 2
            ),
            "esg_rating_change": f"{current['esg_rating']} → {optimized['esg_rating']}",
            "board_diversity_change": round(
                optimized['board_diversity'] - current['board_diversity'], 2
            )
        }
