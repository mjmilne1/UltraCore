"""
UltraCore MCP Integration
Model Context Protocol for tool orchestration
"""

from typing import Dict, List, Any, Callable
import json
import asyncio

# ============================================================================
# MCP TOOL REGISTRY
# ============================================================================

class MCPToolRegistry:
    """MCP tool registry for UltraCore"""
    
    def __init__(self):
        self.tools = {}
        self.register_core_tools()
        
    def register_core_tools(self):
        """Register all UltraCore tools for MCP"""
        
        self.tools = {
            # Payment tools
            "process_payment": {
                "description": "Process a payment through optimal rail",
                "parameters": {
                    "amount": "number",
                    "recipient": "string",
                    "currency": "string",
                    "urgent": "boolean"
                },
                "handler": self.process_payment_handler
            },
            
            # Data mesh tools
            "query_data_mesh": {
                "description": "Query federated data across domains",
                "parameters": {
                    "domains": "array",
                    "query": "object",
                    "join_key": "string"
                },
                "handler": self.query_mesh_handler
            },
            
            # ML tools
            "predict_fraud": {
                "description": "Predict fraud using ML models",
                "parameters": {
                    "transaction": "object",
                    "model_version": "string"
                },
                "handler": self.predict_fraud_handler
            },
            
            # Agent tools
            "invoke_agent": {
                "description": "Invoke specialized AI agent",
                "parameters": {
                    "agent_name": "string",
                    "task": "object",
                    "context": "object"
                },
                "handler": self.invoke_agent_handler
            },
            
            # Risk tools
            "check_constraints": {
                "description": "Check transaction against risk constraints",
                "parameters": {
                    "transaction": "object",
                    "constraint_set": "string"
                },
                "handler": self.check_constraints_handler
            },
            
            # Customer tools
            "get_customer_360": {
                "description": "Get complete customer view from data mesh",
                "parameters": {
                    "customer_id": "string",
                    "include_predictions": "boolean"
                },
                "handler": self.get_customer_360_handler
            }
        }
    
    async def process_payment_handler(self, params: Dict) -> Dict:
        """MCP handler for payment processing"""
        from ultracore.integrated_rl_system import UltraPaymentOrchestrator
        
        orchestrator = UltraPaymentOrchestrator()
        result = await orchestrator.process_payment(params)
        
        return {
            "success": result["status"] == "APPROVED",
            "payment_id": f"PAY_{datetime.now().timestamp()}",
            "details": result
        }
    
    async def query_mesh_handler(self, params: Dict) -> Dict:
        """MCP handler for data mesh queries"""
        from ultracore.mesh.data_mesh import DataMeshOrchestrator
        
        mesh = DataMeshOrchestrator()
        results = await mesh.federated_query(params["query"])
        
        return {
            "data": results,
            "domains_queried": params["domains"],
            "latency_ms": 45  # Example
        }
    
    async def invoke_agent_handler(self, params: Dict) -> Dict:
        """MCP handler for agent invocation"""
        from ultracore.agents.agent_system import AgentSystem
        
        agent_system = AgentSystem()
        result = await agent_system.invoke(
            params["agent_name"],
            params["task"]
        )
        
        return result
    
    def export_for_llm(self) -> List[Dict]:
        """Export tools in MCP format for LLMs"""
        
        mcp_tools = []
        for name, tool in self.tools.items():
            mcp_tools.append({
                "name": name,
                "description": tool["description"],
                "input_schema": {
                    "type": "object",
                    "properties": tool["parameters"],
                    "required": list(tool["parameters"].keys())
                }
            })
        
        return mcp_tools

class MCPOrchestrator:
    """Orchestrate MCP tool calls"""
    
    def __init__(self):
        self.registry = MCPToolRegistry()
        self.context = {}
        
    async def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute MCP tool"""
        
        if tool_name not in self.registry.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.registry.tools[tool_name]
        
        # Validate parameters
        for param, param_type in tool["parameters"].items():
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")
        
        # Execute handler
        result = await tool["handler"](parameters)
        
        # Update context
        self.context[f"{tool_name}_last_result"] = result
        
        return result
    
    async def execute_chain(self, chain: List[Dict]) -> List[Dict]:
        """Execute chain of MCP tool calls"""
        
        results = []
        
        for step in chain:
            # Resolve parameters from context
            params = self.resolve_parameters(step["parameters"])
            
            # Execute tool
            result = await self.execute_tool(step["tool"], params)
            results.append(result)
            
            # Check if we should continue
            if not result.get("success", True):
                break
        
        return results
    
    def resolve_parameters(self, params: Dict) -> Dict:
        """Resolve parameters from context"""
        
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to context
                context_key = value[1:]
                resolved[key] = self.context.get(context_key, value)
            else:
                resolved[key] = value
        
        return resolved
