"""
MCP Tools for ESG Capabilities

This module exposes UltraCore's ESG capabilities as a set of tools that can be
invoked by Manus and other AI agents via the Model Context Protocol (MCP).

These tools turn the ESG module from a passive reporting system into an active,
queryable financial instrument that agents can use to make intelligent decisions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

from ultracore.esg.data.esg_data_loader import EsgDataLoader
from ultracore.esg.agents.epsilon_agent import EpsilonAgent
from ultracore.esg.mcp.portfolio_optimizer import EsgPortfolioOptimizer


class EsgMcpTools:
    """
    MCP tools for ESG capabilities.
    
    These tools enable AI agents to:
    1. Query ESG profiles of securities
    2. Screen portfolios against ESG criteria
    3. Optimize portfolios for ESG objectives
    4. Generate ESG reports
    """
    
    def __init__(self, esg_data_loader: EsgDataLoader, epsilon_agent: Optional[EpsilonAgent] = None, asset_universe: Optional[List[str]] = None):
        self.esg_data_loader = esg_data_loader
        self.epsilon_agent = epsilon_agent
        self.asset_universe = asset_universe or []
        
        # Initialize optimizer if agent is provided
        if epsilon_agent and asset_universe:
            self.optimizer = EsgPortfolioOptimizer(
                esg_data_loader=esg_data_loader,
                epsilon_agent=epsilon_agent,
                asset_universe=asset_universe
            )
        else:
            self.optimizer = None
    
    def get_esg_profile(self, isin: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the complete ESG profile for a given security.
        
        Args:
            isin: International Securities Identification Number
            as_of_date: Optional date (ISO format). If not provided, uses latest data.
        
        Returns:
            Dictionary containing:
            - msci_rating: MSCI ESG rating (AAA-CCC)
            - sustainalytics_score: Sustainalytics ESG risk score (0-100)
            - carbon_intensity: Carbon intensity (tCO2e per $M revenue)
            - water_intensity: Water intensity (m3 per $M revenue)
            - board_diversity: % women on board
            - controversy_score: Controversy score (0-10, lower is better)
            - sdg_alignment: UN SDG alignment scores (dict)
            - excluded_sectors: List of controversial sectors
        
        Example:
            >>> tools.get_esg_profile("AU000000VAS3")
            {
                "isin": "AU000000VAS3",
                "ticker": "VAS",
                "name": "Vanguard Australian Shares Index ETF",
                "msci_rating": "AA",
                "sustainalytics_score": 18.5,
                "carbon_intensity": 125.3,
                "board_diversity": 32.5,
                "controversy_score": 2.1,
                "sdg_alignment": {
                    "SDG_7": 0.65,  # Affordable and Clean Energy
                    "SDG_13": 0.58  # Climate Action
                },
                "last_updated": "2025-11-14T00:00:00Z"
            }
        """
        # Parse date
        if as_of_date:
            date = pd.to_datetime(as_of_date)
        else:
            date = datetime.now()
        
        # Get ESG data
        esg_data = self.esg_data_loader.get_esg_profile(isin, date)
        
        if not esg_data:
            return {
                "error": f"No ESG data found for ISIN: {isin}",
                "isin": isin
            }
        
        return esg_data
    
    def screen_portfolio_esg(
        self,
        portfolio: Dict[str, float],
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Screen a portfolio against ESG criteria and return a compliance report.
        
        Args:
            portfolio: Dict mapping ISIN to weight (e.g., {"AU000000VAS3": 0.5, "AU000000VGS3": 0.5})
            criteria: ESG screening criteria, e.g.:
                {
                    "min_esg_rating": "A",
                    "max_carbon_intensity": 200.0,
                    "excluded_sectors": ["Tobacco", "Weapons"],
                    "min_board_diversity": 30.0
                }
        
        Returns:
            Dictionary containing:
            - compliant: Boolean indicating if portfolio meets all criteria
            - violations: List of violations
            - portfolio_metrics: Aggregated ESG metrics for the portfolio
            - recommendations: Suggested actions to achieve compliance
        
        Example:
            >>> portfolio = {"AU000000VAS3": 0.6, "AU000000VGS3": 0.4}
            >>> criteria = {"min_esg_rating": "A", "max_carbon_intensity": 150.0}
            >>> tools.screen_portfolio_esg(portfolio, criteria)
            {
                "compliant": False,
                "violations": [
                    {
                        "type": "carbon_intensity",
                        "threshold": 150.0,
                        "actual": 187.3,
                        "severity": "medium"
                    }
                ],
                "portfolio_metrics": {
                    "weighted_esg_rating": "AA",
                    "weighted_carbon_intensity": 187.3,
                    "weighted_board_diversity": 35.2
                },
                "recommendations": [
                    "Reduce allocation to high-carbon assets",
                    "Consider increasing allocation to ETHI (carbon intensity: 45.2)"
                ]
            }
        """
        violations = []
        portfolio_metrics = {}
        recommendations = []
        
        # Calculate portfolio-weighted ESG metrics
        total_weight = sum(portfolio.values())
        
        weighted_rating = 0.0
        weighted_carbon = 0.0
        weighted_diversity = 0.0
        
        rating_map = {'AAA': 7, 'AA': 6, 'A': 5, 'BBB': 4, 'BB': 3, 'B': 2, 'CCC': 1}
        
        for isin, weight in portfolio.items():
            normalized_weight = weight / total_weight
            esg_profile = self.get_esg_profile(isin)
            
            if 'error' in esg_profile:
                continue
            
            # Aggregate metrics
            rating_numeric = rating_map.get(esg_profile.get('msci_rating', 'BBB'), 4)
            weighted_rating += normalized_weight * rating_numeric
            weighted_carbon += normalized_weight * esg_profile.get('carbon_intensity', 0)
            weighted_diversity += normalized_weight * esg_profile.get('board_diversity', 0)
            
            # Check for sector exclusions
            if 'excluded_sectors' in criteria:
                asset_sectors = esg_profile.get('sectors', [])
                for excluded in criteria['excluded_sectors']:
                    if excluded in asset_sectors:
                        violations.append({
                            "type": "excluded_sector",
                            "isin": isin,
                            "sector": excluded,
                            "weight": weight,
                            "severity": "high"
                        })
        
        # Convert weighted rating back to letter grade
        rating_letters = {7: 'AAA', 6: 'AA', 5: 'A', 4: 'BBB', 3: 'BB', 2: 'B', 1: 'CCC'}
        portfolio_rating = rating_letters.get(round(weighted_rating), 'BBB')
        
        portfolio_metrics = {
            "weighted_esg_rating": portfolio_rating,
            "weighted_carbon_intensity": round(weighted_carbon, 2),
            "weighted_board_diversity": round(weighted_diversity, 2)
        }
        
        # Check criteria
        if 'min_esg_rating' in criteria:
            min_rating_numeric = rating_map.get(criteria['min_esg_rating'], 4)
            if weighted_rating < min_rating_numeric:
                violations.append({
                    "type": "esg_rating",
                    "threshold": criteria['min_esg_rating'],
                    "actual": portfolio_rating,
                    "severity": "medium"
                })
                recommendations.append(f"Increase allocation to higher-rated ESG assets (A or above)")
        
        if 'max_carbon_intensity' in criteria:
            if weighted_carbon > criteria['max_carbon_intensity']:
                violations.append({
                    "type": "carbon_intensity",
                    "threshold": criteria['max_carbon_intensity'],
                    "actual": round(weighted_carbon, 2),
                    "severity": "medium"
                })
                recommendations.append("Reduce allocation to high-carbon assets")
        
        if 'min_board_diversity' in criteria:
            if weighted_diversity < criteria['min_board_diversity']:
                violations.append({
                    "type": "board_diversity",
                    "threshold": criteria['min_board_diversity'],
                    "actual": round(weighted_diversity, 2),
                    "severity": "low"
                })
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "portfolio_metrics": portfolio_metrics,
            "recommendations": recommendations
        }
    
    def optimize_portfolio_esg(
        self,
        current_portfolio: Dict[str, float],
        objectives: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize a portfolio based on financial and ESG objectives.
        
        This uses the Epsilon Agent (RL) to generate an optimized portfolio that
        balances financial returns with ESG outcomes.
        
        Args:
            current_portfolio: Current portfolio holdings (ISIN -> weight)
            objectives: Optimization objectives, e.g.:
                {
                    "target_return": 0.08,  # 8% annual return
                    "max_volatility": 0.15,  # 15% volatility
                    "esg_weight": 0.4,  # 40% weight on ESG vs financial
                    "target_carbon_reduction": 0.3  # 30% reduction in carbon intensity
                }
            constraints: Optional constraints (same format as screen_portfolio_esg)
        
        Returns:
            Dictionary containing:
            - optimized_portfolio: New portfolio weights
            - expected_return: Expected annual return
            - expected_volatility: Expected volatility
            - esg_improvement: Improvement in ESG metrics
            - trade_list: List of trades to execute
        
        Example:
            >>> current = {"AU000000VAS3": 1.0}
            >>> objectives = {"target_return": 0.10, "esg_weight": 0.5}
            >>> result = tools.optimize_portfolio_esg(current, objectives)
            {
                "optimized_portfolio": {
                    "AU000000VAS3": 0.4,
                    "AU000000ETHI": 0.3,
                    "AU000000VGS3": 0.3
                },
                "expected_return": 0.105,
                "expected_volatility": 0.142,
                "esg_improvement": {
                    "carbon_intensity": -35.2,  # 35.2% reduction
                    "esg_rating": "AA"  # Upgraded from A
                },
                "trade_list": [
                    {"action": "sell", "isin": "AU000000VAS3", "amount": 0.6},
                    {"action": "buy", "isin": "AU000000ETHI", "amount": 0.3},
                    {"action": "buy", "isin": "AU000000VGS3", "amount": 0.3}
                ]
            }
        """
        if not self.optimizer:
            return {
                "error": "Portfolio optimizer not initialized. Requires a trained Epsilon Agent and asset universe."
            }
        
        # Run full RL-powered optimization
        result = self.optimizer.optimize(
            current_portfolio=current_portfolio,
            objectives=objectives,
            constraints=constraints
        )
        
        return result
    
    def generate_esg_report(
        self,
        portfolio: Dict[str, float],
        report_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Generate an ESG report for a portfolio.
        
        Args:
            portfolio: Portfolio holdings (ISIN -> weight)
            report_type: Type of report ("comprehensive", "summary", "regulatory")
        
        Returns:
            Dictionary containing the report data
        """
        # Get portfolio metrics
        screening_result = self.screen_portfolio_esg(portfolio, {})
        
        report = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "portfolio_summary": screening_result['portfolio_metrics'],
            "holdings": []
        }
        
        # Add detailed holdings information
        for isin, weight in portfolio.items():
            esg_profile = self.get_esg_profile(isin)
            if 'error' not in esg_profile:
                report['holdings'].append({
                    "isin": isin,
                    "weight": weight,
                    "esg_profile": esg_profile
                })
        
        return report


# Tool registration for MCP Server
def register_esg_tools(server, esg_data_loader: EsgDataLoader, epsilon_agent: Optional[EpsilonAgent] = None):
    """
    Register ESG tools with the MCP server.
    
    This makes the tools available to Manus and other AI agents.
    """
    tools = EsgMcpTools(esg_data_loader, epsilon_agent)
    
    server.register_tool(
        name="get_esg_profile",
        description="Get the complete ESG profile for a security",
        function=tools.get_esg_profile
    )
    
    server.register_tool(
        name="screen_portfolio_esg",
        description="Screen a portfolio against ESG criteria",
        function=tools.screen_portfolio_esg
    )
    
    server.register_tool(
        name="optimize_portfolio_esg",
        description="Optimize a portfolio for financial and ESG objectives",
        function=tools.optimize_portfolio_esg
    )
    
    server.register_tool(
        name="generate_esg_report",
        description="Generate an ESG report for a portfolio",
        function=tools.generate_esg_report
    )
