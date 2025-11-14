"""
Mock MCP Tools for Testing.

Simulates Model Context Protocol tools for agentic AI testing.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ToolCategory(str, Enum):
    """MCP tool categories."""
    ACCOUNT = "account"
    INVESTMENT = "investment"
    PORTFOLIO = "portfolio"
    ANALYTICS = "analytics"
    OPTIMIZATION = "optimization"


@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]
    handler: Callable


class MockMCPToolRegistry:
    """
    Mock MCP tool registry.
    
    Manages registration and discovery of MCP tools.
    """
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.tool_calls = []
    
    def register_tool(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        parameters: Dict[str, Any],
        handler: Callable
    ):
        """Register an MCP tool."""
        tool = MCPTool(
            name=name,
            description=description,
            category=category,
            parameters=parameters,
            handler=handler
        )
        self.tools[name] = tool
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[MCPTool]:
        """List all tools, optionally filtered by category."""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call an MCP tool."""
        tool = self.get_tool(name)
        
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        
        # Validate arguments
        self._validate_arguments(tool, arguments)
        
        # Record call
        self.tool_calls.append({
            "tool": name,
            "arguments": arguments
        })
        
        # Call handler
        result = await tool.handler(**arguments)
        
        return result
    
    def _validate_arguments(
        self,
        tool: MCPTool,
        arguments: Dict[str, Any]
    ):
        """Validate tool arguments."""
        required_params = [
            p for p, schema in tool.parameters.items()
            if schema.get("required", False)
        ]
        
        for param in required_params:
            if param not in arguments:
                raise ValueError(f"Missing required parameter: {param}")


class MockAccountTools:
    """Mock account management tools."""
    
    def __init__(self, registry: MockMCPToolRegistry):
        self.registry = registry
        self._register_tools()
    
    def _register_tools(self):
        """Register account tools."""
        self.registry.register_tool(
            name="get_account_balance",
            description="Get account balance",
            category=ToolCategory.ACCOUNT,
            parameters={
                "account_id": {"type": "string", "required": True}
            },
            handler=self.get_account_balance
        )
        
        self.registry.register_tool(
            name="create_account",
            description="Create new account",
            category=ToolCategory.ACCOUNT,
            parameters={
                "user_id": {"type": "string", "required": True},
                "account_type": {"type": "string", "required": True}
            },
            handler=self.create_account
        )
    
    async def get_account_balance(self, account_id: str) -> Dict[str, Any]:
        """Get account balance."""
        return {
            "account_id": account_id,
            "balance": 10000.00,
            "currency": "AUD",
            "status": "active"
        }
    
    async def create_account(
        self,
        user_id: str,
        account_type: str
    ) -> Dict[str, Any]:
        """Create new account."""
        return {
            "account_id": f"acc_{user_id[:8]}",
            "user_id": user_id,
            "account_type": account_type,
            "status": "active",
            "created": True
        }


class MockInvestmentPodTools:
    """Mock Investment Pod tools."""
    
    def __init__(self, registry: MockMCPToolRegistry):
        self.registry = registry
        self._register_tools()
    
    def _register_tools(self):
        """Register Investment Pod tools."""
        self.registry.register_tool(
            name="create_investment_pod",
            description="Create new Investment Pod",
            category=ToolCategory.INVESTMENT,
            parameters={
                "user_id": {"type": "string", "required": True},
                "goal_type": {"type": "string", "required": True},
                "target_amount": {"type": "number", "required": True},
                "risk_tolerance": {"type": "string", "required": True}
            },
            handler=self.create_investment_pod
        )
        
        self.registry.register_tool(
            name="get_pod_status",
            description="Get Investment Pod status",
            category=ToolCategory.INVESTMENT,
            parameters={
                "pod_id": {"type": "string", "required": True}
            },
            handler=self.get_pod_status
        )
        
        self.registry.register_tool(
            name="optimize_pod",
            description="Optimize Investment Pod portfolio",
            category=ToolCategory.INVESTMENT,
            parameters={
                "pod_id": {"type": "string", "required": True}
            },
            handler=self.optimize_pod
        )
    
    async def create_investment_pod(
        self,
        user_id: str,
        goal_type: str,
        target_amount: float,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Create Investment Pod."""
        return {
            "pod_id": f"pod_{user_id[:8]}",
            "user_id": user_id,
            "goal_type": goal_type,
            "target_amount": target_amount,
            "risk_tolerance": risk_tolerance,
            "status": "created",
            "created": True
        }
    
    async def get_pod_status(self, pod_id: str) -> Dict[str, Any]:
        """Get Pod status."""
        return {
            "pod_id": pod_id,
            "status": "active",
            "current_value": 15000.00,
            "target_amount": 100000.00,
            "progress": 15.0,
            "total_return_pct": 8.5
        }
    
    async def optimize_pod(self, pod_id: str) -> Dict[str, Any]:
        """Optimize Pod portfolio."""
        return {
            "pod_id": pod_id,
            "optimized": True,
            "target_allocation": {
                "VAS": 0.30,
                "VGS": 0.40,
                "VAF": 0.20,
                "VGB": 0.10
            },
            "expected_return": 0.089,
            "expected_volatility": 0.12,
            "sharpe_ratio": 0.66
        }


class MockUltraOptimiserTools:
    """Mock UltraOptimiser tools."""
    
    def __init__(self, registry: MockMCPToolRegistry):
        self.registry = registry
        self._register_tools()
    
    def _register_tools(self):
        """Register UltraOptimiser tools."""
        self.registry.register_tool(
            name="optimize_portfolio",
            description="Optimize portfolio using UltraOptimiser",
            category=ToolCategory.OPTIMIZATION,
            parameters={
                "risk_tolerance": {"type": "string", "required": True},
                "time_horizon_years": {"type": "number", "required": True},
                "current_holdings": {"type": "object", "required": False},
                "available_cash": {"type": "number", "required": True}
            },
            handler=self.optimize_portfolio
        )
        
        self.registry.register_tool(
            name="check_rebalancing",
            description="Check if portfolio needs rebalancing",
            category=ToolCategory.OPTIMIZATION,
            parameters={
                "current_allocation": {"type": "object", "required": True},
                "target_allocation": {"type": "object", "required": True}
            },
            handler=self.check_rebalancing
        )
    
    async def optimize_portfolio(
        self,
        risk_tolerance: str,
        time_horizon_years: int,
        current_holdings: Optional[Dict] = None,
        available_cash: float = 0
    ) -> Dict[str, Any]:
        """Optimize portfolio."""
        return {
            "optimized": True,
            "target_allocation": {
                "VAS": 0.25,
                "VGS": 0.35,
                "NDQ": 0.15,
                "VAF": 0.15,
                "VGB": 0.10
            },
            "expected_return": 0.089,
            "sharpe_ratio": 0.66,
            "max_drawdown": -0.1523
        }
    
    async def check_rebalancing(
        self,
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float]
    ) -> Dict[str, Any]:
        """Check rebalancing."""
        # Calculate drift
        drift = sum(
            abs(current_allocation.get(k, 0) - target_allocation.get(k, 0))
            for k in set(list(current_allocation.keys()) + list(target_allocation.keys()))
        )
        
        needs_rebalancing = drift > 0.05
        
        return {
            "needs_rebalancing": needs_rebalancing,
            "drift": drift,
            "threshold": 0.05,
            "recommendation": "Rebalance recommended" if needs_rebalancing else "Portfolio within tolerance"
        }


class MockInvestmentOrchestrator:
    """
    Mock investment orchestrator.
    
    Orchestrates multiple MCP tools to execute investment workflows.
    """
    
    def __init__(self, registry: MockMCPToolRegistry):
        self.registry = registry
        self.workflows_executed = []
    
    async def execute_pod_creation_workflow(
        self,
        user_id: str,
        goal_type: str,
        target_amount: float,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        Execute complete Pod creation workflow.
        
        Steps:
        1. Create Investment Pod
        2. Optimize portfolio
        3. Return result
        """
        workflow_id = f"workflow_{len(self.workflows_executed)}"
        
        # Step 1: Create Pod
        pod_result = await self.registry.call_tool(
            "create_investment_pod",
            {
                "user_id": user_id,
                "goal_type": goal_type,
                "target_amount": target_amount,
                "risk_tolerance": risk_tolerance
            }
        )
        
        pod_id = pod_result["pod_id"]
        
        # Step 2: Optimize
        optimize_result = await self.registry.call_tool(
            "optimize_pod",
            {"pod_id": pod_id}
        )
        
        # Record workflow
        self.workflows_executed.append({
            "workflow_id": workflow_id,
            "type": "pod_creation",
            "steps": ["create_pod", "optimize_pod"],
            "result": "success"
        })
        
        return {
            "workflow_id": workflow_id,
            "pod_id": pod_id,
            "optimized": True,
            "target_allocation": optimize_result["target_allocation"],
            "expected_return": optimize_result["expected_return"]
        }
    
    async def execute_rebalancing_workflow(
        self,
        pod_id: str
    ) -> Dict[str, Any]:
        """
        Execute rebalancing workflow.
        
        Steps:
        1. Get Pod status
        2. Check if rebalancing needed
        3. Optimize if needed
        4. Return result
        """
        workflow_id = f"workflow_{len(self.workflows_executed)}"
        
        # Step 1: Get status
        status = await self.registry.call_tool(
            "get_pod_status",
            {"pod_id": pod_id}
        )
        
        # Step 2: Check rebalancing (simplified)
        needs_rebalancing = True  # Simplified for testing
        
        # Step 3: Optimize if needed
        if needs_rebalancing:
            optimize_result = await self.registry.call_tool(
                "optimize_pod",
                {"pod_id": pod_id}
            )
            
            result = {
                "workflow_id": workflow_id,
                "pod_id": pod_id,
                "rebalanced": True,
                "new_allocation": optimize_result["target_allocation"]
            }
        else:
            result = {
                "workflow_id": workflow_id,
                "pod_id": pod_id,
                "rebalanced": False,
                "message": "No rebalancing needed"
            }
        
        # Record workflow
        self.workflows_executed.append({
            "workflow_id": workflow_id,
            "type": "rebalancing",
            "steps": ["get_status", "check_rebalancing", "optimize"],
            "result": "success"
        })
        
        return result


def create_mock_mcp_environment() -> tuple[MockMCPToolRegistry, MockInvestmentOrchestrator]:
    """
    Create complete mock MCP environment for testing.
    
    Returns:
        (registry, orchestrator)
    """
    registry = MockMCPToolRegistry()
    
    # Register all tools
    MockAccountTools(registry)
    MockInvestmentPodTools(registry)
    MockUltraOptimiserTools(registry)
    
    # Create orchestrator
    orchestrator = MockInvestmentOrchestrator(registry)
    
    return registry, orchestrator
