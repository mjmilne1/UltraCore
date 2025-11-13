"""
Investment Pods MCP Tools
Model Context Protocol tools for external integrations
"""

from decimal import Decimal
from datetime import date, datetime
from typing import Dict, List, Optional
import json


class PodMCPTools:
    """
    MCP tools for Investment Pods system
    
    6 core functions for external integrations
    """
    
    def __init__(self, pod_service):
        self.pod_service = pod_service
    
    def create_goal_pod(
        self,
        client_id: str,
        goal_type: str,
        goal_name: str,
        target_amount: float,
        target_date: str,
        risk_tolerance: int,
        monthly_contribution: float
    ) -> Dict:
        """
        Create a new goal-based investment Pod
        
        Args:
            client_id: Client identifier
            goal_type: Type of goal (first_home, retirement, wealth_accumulation, etc.)
            goal_name: Name of the goal
            target_amount: Target amount in AUD
            target_date: Target date (ISO format: YYYY-MM-DD)
            risk_tolerance: Risk tolerance (1-7 scale)
            monthly_contribution: Monthly contribution amount
        
        Returns:
            Dict with pod_id, optimization_result, and anya_response
        """
        result = self.pod_service.create_pod(
            client_id=client_id,
            goal_type=goal_type,
            goal_name=goal_name,
            target_amount=Decimal(str(target_amount)),
            target_date=datetime.fromisoformat(target_date).date(),
            risk_tolerance=risk_tolerance,
            monthly_contribution=Decimal(str(monthly_contribution))
        )
        
        return {
            "pod_id": result["pod"].pod_id,
            "status": "created",
            "allocation": [
                {
                    "etf_code": etf["etf_code"],
                    "etf_name": etf["etf_name"],
                    "weight": float(etf["weight"])
                }
                for etf in result["optimization_result"]["allocation"]
            ],
            "expected_return": float(result["optimization_result"]["metrics"]["expected_return"]),
            "expected_volatility": float(result["optimization_result"]["metrics"]["expected_volatility"]),
            "sharpe_ratio": float(result["optimization_result"]["metrics"]["sharpe_ratio"]),
            "anya_message": result["anya_response"]
        }
    
    def optimize_pod_allocation(
        self,
        pod_id: str,
        reason: str = "parameter_change"
    ) -> Dict:
        """
        Re-optimize Pod allocation
        
        Args:
            pod_id: Pod identifier
            reason: Reason for re-optimization (parameter_change, glide_path, market_change)
        
        Returns:
            Dict with new allocation and metrics
        """
        result = self.pod_service.optimize_pod(pod_id, reason)
        
        return {
            "pod_id": pod_id,
            "optimization_id": result["optimization_id"],
            "new_allocation": [
                {
                    "etf_code": etf["etf_code"],
                    "weight": float(etf["weight"])
                }
                for etf in result["allocation"]
            ],
            "expected_return": float(result["metrics"]["expected_return"]),
            "sharpe_ratio": float(result["metrics"]["sharpe_ratio"]),
            "optimization_reason": reason
        }
    
    def calculate_glide_path(
        self,
        goal_type: str,
        target_date: str,
        current_date: Optional[str] = None
    ) -> Dict:
        """
        Calculate glide path schedule for a goal
        
        Args:
            goal_type: Type of goal
            target_date: Target date (ISO format)
            current_date: Current date (optional, defaults to today)
        
        Returns:
            Dict with glide path schedule and transitions
        """
        from ..services.glide_path_engine import GlidePathEngine
        from ..events import GoalType
        
        engine = GlidePathEngine()
        
        goal_type_enum = GoalType[goal_type.upper()]
        target = datetime.fromisoformat(target_date).date()
        current = datetime.fromisoformat(current_date).date() if current_date else date.today()
        
        schedule = engine.calculate_glide_path_schedule(goal_type_enum, target, current)
        current_allocation = engine.calculate_current_allocation(goal_type_enum, target, current)
        
        return {
            "goal_type": goal_type,
            "current_allocation": {
                "equity": float(current_allocation["equity"]),
                "defensive": float(current_allocation["defensive"])
            },
            "transitions": [
                {
                    "date": t.transition_date.isoformat(),
                    "years_remaining": t.years_remaining,
                    "equity_weight": float(t.equity_weight),
                    "defensive_weight": float(t.defensive_weight)
                }
                for t in schedule
            ]
        }
    
    def monitor_downside_risk(
        self,
        pod_id: str
    ) -> Dict:
        """
        Monitor downside risk for a Pod
        
        Args:
            pod_id: Pod identifier
        
        Returns:
            Dict with risk metrics and circuit breaker status
        """
        result = self.pod_service.check_downside_risk(pod_id)
        
        return {
            "pod_id": pod_id,
            "current_drawdown": float(result["current_drawdown"]),
            "max_allowed_drawdown": float(result["max_allowed_drawdown"]),
            "risk_level": result["risk_level"],
            "circuit_breaker_distance": float(result["circuit_breaker_distance"]),
            "circuit_breaker_triggered": result["circuit_breaker_triggered"],
            "action_required": result["action_required"]
        }
    
    def execute_defensive_shift(
        self,
        pod_id: str,
        trigger_reason: str
    ) -> Dict:
        """
        Execute defensive shift (circuit breaker)
        
        Args:
            pod_id: Pod identifier
            trigger_reason: Reason for triggering (downside_breach, volatility_spike)
        
        Returns:
            Dict with defensive shift details
        """
        result = self.pod_service.trigger_circuit_breaker(pod_id, trigger_reason)
        
        return {
            "pod_id": pod_id,
            "circuit_breaker_id": result["circuit_breaker_id"],
            "trigger_reason": trigger_reason,
            "defensive_allocation": {
                "equity": float(result["defensive_allocation"]["equity"]),
                "defensive": float(result["defensive_allocation"]["defensive"])
            },
            "trades_executed": result["trades_executed"],
            "client_notified": result["client_notified"],
            "anya_message": result["anya_message"]
        }
    
    def calculate_required_return(
        self,
        current_value: float,
        target_value: float,
        monthly_contribution: float,
        months_to_goal: int
    ) -> Dict:
        """
        Calculate required return to reach goal
        
        Args:
            current_value: Current portfolio value
            target_value: Target value
            monthly_contribution: Monthly contribution amount
            months_to_goal: Number of months to goal
        
        Returns:
            Dict with required return and analysis
        """
        from ..services.portfolio_optimizer import PortfolioOptimizer
        
        optimizer = PortfolioOptimizer()
        
        required_return = optimizer.calculate_required_return(
            current_value=Decimal(str(current_value)),
            target_value=Decimal(str(target_value)),
            monthly_contribution=Decimal(str(monthly_contribution)),
            months_to_goal=months_to_goal
        )
        
        # Assess feasibility
        if required_return < Decimal("6.0"):
            feasibility = "highly_achievable"
        elif required_return < Decimal("10.0"):
            feasibility = "achievable"
        elif required_return < Decimal("15.0"):
            feasibility = "challenging"
        else:
            feasibility = "unrealistic"
        
        return {
            "required_annual_return": float(required_return),
            "feasibility": feasibility,
            "current_value": current_value,
            "target_value": target_value,
            "monthly_contribution": monthly_contribution,
            "months_to_goal": months_to_goal,
            "recommendation": self._get_return_recommendation(required_return)
        }
    
    def _get_return_recommendation(self, required_return: Decimal) -> str:
        """Get recommendation based on required return"""
        if required_return < Decimal("6.0"):
            return "Your goal is very achievable with a conservative portfolio"
        elif required_return < Decimal("10.0"):
            return "Your goal is achievable with a balanced portfolio"
        elif required_return < Decimal("15.0"):
            return "Your goal is challenging - consider increasing contributions or extending timeline"
        else:
            return "Your goal may be unrealistic - please adjust target amount, timeline, or contributions"


# MCP tool registry
MCP_TOOLS = {
    "create_goal_pod": {
        "description": "Create a new goal-based investment Pod",
        "parameters": {
            "client_id": "string",
            "goal_type": "string (first_home, retirement, wealth_accumulation, etc.)",
            "goal_name": "string",
            "target_amount": "float (AUD)",
            "target_date": "string (ISO format: YYYY-MM-DD)",
            "risk_tolerance": "int (1-7 scale)",
            "monthly_contribution": "float (AUD)"
        }
    },
    "optimize_pod_allocation": {
        "description": "Re-optimize Pod allocation",
        "parameters": {
            "pod_id": "string",
            "reason": "string (parameter_change, glide_path, market_change)"
        }
    },
    "calculate_glide_path": {
        "description": "Calculate glide path schedule for a goal",
        "parameters": {
            "goal_type": "string",
            "target_date": "string (ISO format)",
            "current_date": "string (optional, ISO format)"
        }
    },
    "monitor_downside_risk": {
        "description": "Monitor downside risk for a Pod",
        "parameters": {
            "pod_id": "string"
        }
    },
    "execute_defensive_shift": {
        "description": "Execute defensive shift (circuit breaker)",
        "parameters": {
            "pod_id": "string",
            "trigger_reason": "string (downside_breach, volatility_spike)"
        }
    },
    "calculate_required_return": {
        "description": "Calculate required return to reach goal",
        "parameters": {
            "current_value": "float (AUD)",
            "target_value": "float (AUD)",
            "monthly_contribution": "float (AUD)",
            "months_to_goal": "int"
        }
    }
}
