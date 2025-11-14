"""
Anya AI Agent

Real AI agent using OpenAI with MCP tool integration for intelligent banking operations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from ultracore.ai.openai_client import AIClientFactory
from ultracore.ai.mcp.tools import MCPTools, MCPToolExecutor


class AnyaAgent:
    """
    Anya - AI Banking Agent
    
    Intelligent agent that can:
    - Answer customer queries
    - Execute banking operations via MCP tools
    - Provide financial advice
    - Detect fraud and anomalies
    - Assist with account management
    """
    
    SYSTEM_PROMPT = """You are Anya, an intelligent AI banking assistant for UltraCore.

You help customers with:
- Account inquiries and management
- Transaction execution and history
- Loan eligibility and applications
- Fraud detection and security
- Financial advice and planning

You have access to the following tools:
- get_customer_360: Get comprehensive customer information
- check_loan_eligibility: Check if customer qualifies for a loan
- get_account_balance: Get current account balance
- analyze_credit_risk: Analyze customer credit risk
- get_trial_balance: Get accounting trial balance
- execute_transaction: Execute financial transactions
- detect_fraud: Detect potential fraud
- check_access_control: Check user access permissions

Always:
- Be professional and helpful
- Explain financial concepts clearly
- Prioritize security and compliance
- Use tools when needed to get accurate data
- Provide actionable recommendations

Never:
- Share sensitive customer data inappropriately
- Execute transactions without clear user intent
- Make guarantees about loan approvals
- Bypass security checks
"""
    
    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        tool_executor: Optional[MCPToolExecutor] = None
    ):
        self.model = model
        self.client = AIClientFactory.get_client(model=model)
        self.tool_executor = tool_executor or MCPToolExecutor()
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    async def chat(
        self,
        user_id: str,
        message: str,
        tenant_id: str,
        use_tools: bool = True,
        max_tool_calls: int = 5
    ) -> Dict[str, Any]:
        """
        Chat with Anya.
        
        Args:
            user_id: User ID for conversation context
            message: User's message
            tenant_id: Tenant ID for tool execution
            use_tools: Whether to use MCP tools
            max_tool_calls: Maximum number of tool calls per conversation
        
        Returns:
            Response dict with 'message', 'tool_calls', 'usage'
        """
        # Get or create conversation history
        conversation_key = f"{tenant_id}:{user_id}"
        if conversation_key not in self.conversation_history:
            self.conversation_history[conversation_key] = []
        
        context = self.conversation_history[conversation_key]
        
        # Prepare tools if enabled
        functions = MCPTools.get_tool_definitions() if use_tools else None
        
        # Get response
        tool_calls_made = []
        response_message = None
        
        for iteration in range(max_tool_calls):
            # Call OpenAI
            response = await self.client.chat_with_context(
                user_message=message if iteration == 0 else None,
                context=context,
                system_prompt=self.SYSTEM_PROMPT if iteration == 0 else None,
                functions=functions,
                temperature=0.7
            )
            
            # Check if function call was made
            if "function_call" in response:
                function_call = response["function_call"]
                tool_name = function_call["name"]
                arguments = function_call["arguments"]
                
                # Add tenant_id to arguments if not present
                if "tenant_id" not in arguments:
                    arguments["tenant_id"] = tenant_id
                
                # Execute tool
                tool_result = await self.tool_executor.execute_tool(
                    tool_name=tool_name,
                    arguments=arguments
                )
                
                # Track tool call
                tool_calls_made.append({
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": tool_result
                })
                
                # Add function call and result to context
                context.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments)
                    }
                })
                context.append({
                    "role": "function",
                    "name": tool_name,
                    "content": json.dumps(tool_result)
                })
                
                # Continue to get final response
                continue
            
            # No function call - we have the final response
            response_message = response["content"]
            break
        
        # Add final exchange to history
        if response_message:
            context.append({"role": "user", "content": message})
            context.append({"role": "assistant", "content": response_message})
        
        # Trim context if too long (keep last 20 messages)
        if len(context) > 20:
            context = context[-20:]
        
        self.conversation_history[conversation_key] = context
        
        return {
            "message": response_message or "I apologize, I couldn't complete that request.",
            "tool_calls": tool_calls_made,
            "usage": response.get("usage", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def execute_task(
        self,
        task: str,
        tenant_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a specific task.
        
        Args:
            task: Task description
            tenant_id: Tenant ID
            context: Additional context for the task
        
        Returns:
            Task execution result
        """
        # Create a temporary user ID for task execution
        task_user_id = f"task_{datetime.utcnow().timestamp()}"
        
        # Add context to message if provided
        message = task
        if context:
            message += f"\n\nContext: {json.dumps(context, indent=2)}"
        
        # Execute task as a chat
        return await self.chat(
            user_id=task_user_id,
            message=message,
            tenant_id=tenant_id,
            use_tools=True
        )
    
    def clear_conversation(self, user_id: str, tenant_id: str):
        """Clear conversation history for a user"""
        conversation_key = f"{tenant_id}:{user_id}"
        if conversation_key in self.conversation_history:
            del self.conversation_history[conversation_key]
    
    def get_conversation_history(
        self,
        user_id: str,
        tenant_id: str
    ) -> List[Dict[str, str]]:
        """Get conversation history for a user"""
        conversation_key = f"{tenant_id}:{user_id}"
        return self.conversation_history.get(conversation_key, [])


class AnyaDomainAgent(AnyaAgent):
    """
    Domain-specific Anya agent.
    
    Specialized for a specific domain (e.g., accounts, lending, payments).
    """
    
    def __init__(
        self,
        domain: str,
        domain_prompt: str,
        model: str = "gpt-4.1-mini",
        tool_executor: Optional[MCPToolExecutor] = None
    ):
        super().__init__(model=model, tool_executor=tool_executor)
        self.domain = domain
        self.domain_prompt = domain_prompt
        
        # Override system prompt with domain-specific version
        self.SYSTEM_PROMPT = f"""{self.SYSTEM_PROMPT}

DOMAIN SPECIALIZATION: {domain}
{domain_prompt}
"""


# Pre-configured domain agents
class AnyaAccountsAgent(AnyaDomainAgent):
    """Anya agent specialized for account management"""
    
    def __init__(self, **kwargs):
        super().__init__(
            domain="Accounts",
            domain_prompt="""You specialize in:
- Account opening and KYC verification
- Account balance inquiries
- Account status and lifecycle management
- Interest calculations
- Account fraud detection

Focus on providing accurate account information and helping customers manage their accounts effectively.""",
            **kwargs
        )


class AnyaLendingAgent(AnyaDomainAgent):
    """Anya agent specialized for lending"""
    
    def __init__(self, **kwargs):
        super().__init__(
            domain="Lending",
            domain_prompt="""You specialize in:
- Loan eligibility assessment
- Credit risk analysis
- Loan application processing
- Loan restructuring
- Payment schedules

Focus on helping customers understand loan options and guiding them through the application process.""",
            **kwargs
        )


class AnyaPaymentsAgent(AnyaDomainAgent):
    """Anya agent specialized for payments"""
    
    def __init__(self, **kwargs):
        super().__init__(
            domain="Payments",
            domain_prompt="""You specialize in:
- Payment execution and routing
- Transaction history
- Payment fraud detection
- Payment reconciliation
- International transfers

Focus on ensuring secure and efficient payment processing.""",
            **kwargs
        )


class AnyaWealthAgent(AnyaDomainAgent):
    """Anya agent specialized for wealth management"""
    
    def __init__(self, **kwargs):
        super().__init__(
            domain="Wealth",
            domain_prompt="""You specialize in:
- Portfolio management and analysis
- Investment recommendations
- Asset allocation
- Portfolio rebalancing
- Performance tracking

Focus on helping customers optimize their investment portfolios.""",
            **kwargs
        )


class AnyaSecurityAgent(AnyaDomainAgent):
    """Anya agent specialized for security"""
    
    def __init__(self, **kwargs):
        super().__init__(
            domain="Security",
            domain_prompt="""You specialize in:
- Fraud detection and prevention
- Access control decisions
- Anomaly detection
- Threat analysis
- Security incident response

Focus on protecting customers and the platform from security threats.""",
            **kwargs
        )
