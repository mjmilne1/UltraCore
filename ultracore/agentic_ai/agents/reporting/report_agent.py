"""
Report Generation AI Agent
Intelligent agent for report generation, insights, and optimization
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ultracore.reporting.events import ReportType, ReportFormat


@dataclass
class ReportGenerationAgent:
    """
    AI Agent for Intelligent Report Generation
    
    Capabilities:
    - Smart report template selection
    - Automated insights generation
    - Performance narrative creation
    - Tax optimization recommendations
    - Report personalization
    - Delivery time optimization
    """
    
    agent_id: str = "report_generation_agent"
    version: str = "1.0.0"
    
    def select_optimal_template(
        self,
        report_type: ReportType,
        client_data: Dict[str, Any],
        historical_preferences: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select optimal report template based on client profile and preferences
        
        Uses AI to analyze:
        - Client sophistication level
        - Historical template engagement
        - Report type requirements
        - Regulatory requirements
        
        Returns:
            {
                "template_id": str,
                "confidence": float,
                "reasoning": str
            }
        """
        # AI logic would go here
        # For now, return a basic recommendation
        
        sophistication_level = client_data.get("sophistication_level", "medium")
        
        if sophistication_level == "high":
            template_type = "detailed"
        elif sophistication_level == "low":
            template_type = "simplified"
        else:
            template_type = "standard"
        
        return {
            "template_id": f"{report_type.value}_{template_type}",
            "confidence": 0.85,
            "reasoning": f"Selected {template_type} template based on client sophistication level"
        }
    
    def generate_insights(
        self,
        portfolio_data: Dict[str, Any],
        performance_data: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered insights for report
        
        Insights include:
        - Performance attribution
        - Risk analysis
        - Opportunity identification
        - Benchmark comparison
        - Trend analysis
        
        Returns:
            List of insights with priority and confidence
        """
        insights = []
        
        # Performance insight
        total_return = performance_data.get("total_return", 0.0)
        benchmark_return = market_data.get("benchmark_return", 0.0)
        
        if total_return > benchmark_return:
            insights.append({
                "type": "performance",
                "priority": "high",
                "confidence": 0.95,
                "title": "Outperforming Benchmark",
                "description": f"Portfolio returned {total_return:.2%} vs benchmark {benchmark_return:.2%}",
                "recommendation": "Continue current strategy"
            })
        
        # Risk insight
        volatility = performance_data.get("volatility", 0.0)
        if volatility > 0.20:  # >20% volatility
            insights.append({
                "type": "risk",
                "priority": "medium",
                "confidence": 0.90,
                "title": "Elevated Volatility",
                "description": f"Portfolio volatility at {volatility:.2%}",
                "recommendation": "Consider diversification to reduce risk"
            })
        
        # Allocation insight
        allocation = portfolio_data.get("allocation", {})
        if allocation.get("cash", 0.0) > 0.15:  # >15% cash
            insights.append({
                "type": "allocation",
                "priority": "low",
                "confidence": 0.80,
                "title": "High Cash Allocation",
                "description": f"Cash represents {allocation.get('cash', 0.0):.2%} of portfolio",
                "recommendation": "Consider deploying excess cash"
            })
        
        return sorted(insights, key=lambda x: x["priority"], reverse=True)
    
    def generate_performance_narrative(
        self,
        performance_data: Dict[str, Any],
        period: str
    ) -> str:
        """
        Generate natural language narrative for performance
        
        Uses AI to create human-readable performance summary
        
        Returns:
            Performance narrative text
        """
        total_return = performance_data.get("total_return", 0.0)
        sharpe_ratio = performance_data.get("sharpe_ratio", 0.0)
        max_drawdown = performance_data.get("max_drawdown", 0.0)
        
        narrative = f"During the {period} period, your portfolio "
        
        if total_return > 0:
            narrative += f"generated a positive return of {total_return:.2%}. "
        else:
            narrative += f"experienced a decline of {abs(total_return):.2%}. "
        
        if sharpe_ratio > 1.0:
            narrative += f"The risk-adjusted return (Sharpe ratio of {sharpe_ratio:.2f}) indicates strong performance relative to volatility. "
        elif sharpe_ratio < 0:
            narrative += f"The negative Sharpe ratio ({sharpe_ratio:.2f}) suggests returns did not compensate for risk taken. "
        
        if max_drawdown < -0.10:
            narrative += f"The maximum drawdown of {abs(max_drawdown):.2%} represents the largest peak-to-trough decline during this period."
        
        return narrative
    
    def generate_tax_optimization_recommendations(
        self,
        portfolio_data: Dict[str, Any],
        tax_data: Dict[str, Any],
        client_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered tax optimization recommendations
        
        Australian tax optimization strategies:
        - CGT discount timing (12-month holding period)
        - Franking credit utilization
        - Tax loss harvesting
        - Income smoothing
        
        Returns:
            List of tax optimization recommendations
        """
        recommendations = []
        
        # CGT discount recommendation
        holdings = portfolio_data.get("holdings", [])
        for holding in holdings:
            days_held = holding.get("days_held", 0)
            unrealized_gain = holding.get("unrealized_gain", 0.0)
            
            if 330 < days_held < 365 and unrealized_gain > 0:
                recommendations.append({
                    "type": "cgt_discount",
                    "priority": "high",
                    "symbol": holding.get("symbol"),
                    "title": "Approaching CGT Discount",
                    "description": f"{holding.get('symbol')} will qualify for 50% CGT discount in {365 - days_held} days",
                    "potential_saving": unrealized_gain * 0.50 * client_data.get("marginal_tax_rate", 0.37),
                    "action": "Consider holding until CGT discount applies"
                })
        
        # Tax loss harvesting
        for holding in holdings:
            unrealized_loss = holding.get("unrealized_loss", 0.0)
            if unrealized_loss < -1000:  # Significant loss
                recommendations.append({
                    "type": "tax_loss_harvesting",
                    "priority": "medium",
                    "symbol": holding.get("symbol"),
                    "title": "Tax Loss Harvesting Opportunity",
                    "description": f"Realize ${abs(unrealized_loss):.2f} loss to offset gains",
                    "potential_saving": abs(unrealized_loss) * client_data.get("marginal_tax_rate", 0.37),
                    "action": "Consider selling to harvest tax loss"
                })
        
        return sorted(recommendations, key=lambda x: x.get("potential_saving", 0), reverse=True)
    
    def personalize_report(
        self,
        template_data: Dict[str, Any],
        client_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Personalize report based on client preferences
        
        Personalization factors:
        - Preferred metrics
        - Detail level
        - Chart types
        - Language/terminology
        - Focus areas
        
        Returns:
            Personalized report configuration
        """
        personalized = template_data.copy()
        
        # Adjust detail level
        detail_level = client_preferences.get("detail_level", "medium")
        if detail_level == "high":
            personalized["include_detailed_holdings"] = True
            personalized["include_transaction_details"] = True
        elif detail_level == "low":
            personalized["include_detailed_holdings"] = False
            personalized["include_transaction_details"] = False
        
        # Preferred metrics
        preferred_metrics = client_preferences.get("preferred_metrics", [])
        if preferred_metrics:
            personalized["metrics"] = preferred_metrics
        
        # Chart preferences
        chart_type = client_preferences.get("chart_type", "line")
        personalized["chart_type"] = chart_type
        
        return personalized
    
    def optimize_delivery_time(
        self,
        report_type: ReportType,
        frequency: str,
        client_timezone: str,
        historical_engagement: List[Dict[str, Any]]
    ) -> datetime:
        """
        Optimize report delivery time based on engagement patterns
        
        Analyzes:
        - Historical open times
        - Timezone
        - Report type
        - Day of week patterns
        
        Returns:
            Optimal delivery datetime
        """
        # Analyze historical engagement
        if historical_engagement:
            open_hours = [e.get("open_hour", 9) for e in historical_engagement if e.get("opened")]
            avg_open_hour = sum(open_hours) / len(open_hours) if open_hours else 9
        else:
            avg_open_hour = 9  # Default to 9 AM
        
        # Calculate next delivery time
        now = datetime.utcnow()
        
        if frequency == "daily":
            next_delivery = now + timedelta(days=1)
        elif frequency == "weekly":
            next_delivery = now + timedelta(weeks=1)
        elif frequency == "monthly":
            next_delivery = now + timedelta(days=30)
        else:
            next_delivery = now
        
        # Set to optimal hour
        next_delivery = next_delivery.replace(hour=int(avg_open_hour), minute=0, second=0)
        
        return next_delivery
    
    def suggest_report_sections(
        self,
        report_type: ReportType,
        client_data: Dict[str, Any],
        portfolio_data: Dict[str, Any]
    ) -> List[str]:
        """
        Suggest optimal report sections based on context
        
        Returns:
            List of recommended section names
        """
        sections = ["executive_summary"]
        
        if report_type == ReportType.PORTFOLIO_PERFORMANCE:
            sections.extend([
                "performance_overview",
                "holdings_summary",
                "allocation_analysis",
                "performance_attribution"
            ])
            
            if portfolio_data.get("has_options", False):
                sections.append("options_analysis")
            
            if client_data.get("risk_profile") == "high":
                sections.append("risk_metrics")
        
        elif report_type == ReportType.TAX_REPORT:
            sections.extend([
                "capital_gains_summary",
                "dividend_income",
                "tax_optimization_recommendations"
            ])
            
            if client_data.get("has_foreign_investments", False):
                sections.append("foreign_income")
        
        sections.append("appendix")
        
        return sections


# Global instance
_agent = None

def get_report_generation_agent() -> ReportGenerationAgent:
    """Get global report generation agent instance"""
    global _agent
    if _agent is None:
        _agent = ReportGenerationAgent()
    return _agent
