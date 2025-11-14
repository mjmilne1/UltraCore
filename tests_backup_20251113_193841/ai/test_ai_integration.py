"""
AI Integration Tests

Tests for OpenAI client, MCP tools, and Anya agents.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ultracore.ai.openai_client import OpenAIClient, AIClientFactory
from ultracore.ai.mcp.tools import MCPTools, MCPToolExecutor
from ultracore.ai.agents.anya_agent import (
    AnyaAgent,
    AnyaAccountsAgent,
    AnyaLendingAgent,
    AnyaSecurityAgent
)


class TestMCPTools:
    """Test MCP tool definitions"""
    
    def test_get_tool_definitions(self):
        """Test getting all tool definitions"""
        tools = MCPTools.get_tool_definitions()
        
        assert len(tools) >= 8
        assert all("name" in tool for tool in tools)
        assert all("description" in tool for tool in tools)
        assert all("parameters" in tool for tool in tools)
    
    def test_get_tool_by_name(self):
        """Test getting specific tool"""
        tool = MCPTools.get_tool_by_name("get_customer_360")
        
        assert tool is not None
        assert tool["name"] == "get_customer_360"
        assert "tenant_id" in tool["parameters"]["properties"]
        assert "customer_id" in tool["parameters"]["properties"]
    
    def test_get_tool_names(self):
        """Test getting tool names"""
        names = MCPTools.get_tool_names()
        
        assert "get_customer_360" in names
        assert "check_loan_eligibility" in names
        assert "get_account_balance" in names
        assert "detect_fraud" in names


class TestMCPToolExecutor:
    """Test MCP tool executor"""
    
    @pytest.fixture
    def executor(self):
        """Create tool executor"""
        return MCPToolExecutor()
    
    @pytest.mark.asyncio
    async def test_get_customer_360(self, executor):
        """Test customer 360 tool"""
        result = await executor.execute_tool(
            "get_customer_360",
            {
                "tenant_id": "tenant_1",
                "customer_id": "cust_123",
                "include_transactions": True
            }
        )
        
        assert "customer_id" in result
        assert result["customer_id"] == "cust_123"
        assert "accounts" in result
    
    @pytest.mark.asyncio
    async def test_check_loan_eligibility(self, executor):
        """Test loan eligibility tool"""
        result = await executor.execute_tool(
            "check_loan_eligibility",
            {
                "tenant_id": "tenant_1",
                "customer_id": "cust_123",
                "loan_amount": 50000.0,
                "loan_purpose": "home"
            }
        )
        
        assert "eligible" in result
        assert "credit_score" in result
        assert "recommended_rate" in result
    
    @pytest.mark.asyncio
    async def test_get_account_balance(self, executor):
        """Test account balance tool"""
        # Create mock savings service
        mock_account = Mock()
        mock_account.balance = 10000.0
        mock_account.status = "active"
        
        mock_service = AsyncMock()
        mock_service.get_account.return_value = mock_account
        
        executor.savings_service = mock_service
        
        result = await executor.execute_tool(
            "get_account_balance",
            {
                "tenant_id": "tenant_1",
                "account_id": "acc_123"
            }
        )
        
        assert "account_id" in result
        assert "balance" in result
        assert result["balance"] == 10000.0
    
    @pytest.mark.asyncio
    async def test_unknown_tool(self, executor):
        """Test unknown tool handling"""
        result = await executor.execute_tool(
            "unknown_tool",
            {}
        )
        
        assert "error" in result


class TestOpenAIClient:
    """Test OpenAI client (mocked)"""
    
    @pytest.mark.asyncio
    @patch('ultracore.ai.openai_client.AsyncOpenAI')
    async def test_chat_completion(self, mock_openai):
        """Test chat completion"""
        # Mock response
        mock_message = Mock()
        mock_message.content = "Hello! How can I help you?"
        mock_message.role = "assistant"
        mock_message.function_call = None
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create client
        client = OpenAIClient(api_key="test_key")
        client.client = mock_client
        
        # Test completion
        result = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}]
        )
        
        assert result["content"] == "Hello! How can I help you?"
        assert result["role"] == "assistant"
        assert "usage" in result
    
    @pytest.mark.asyncio
    @patch('ultracore.ai.openai_client.AsyncOpenAI')
    async def test_function_call(self, mock_openai):
        """Test function calling"""
        # Mock function call response
        mock_function_call = Mock()
        mock_function_call.name = "get_account_balance"
        mock_function_call.arguments = '{"account_id": "123"}'
        
        mock_choice = Mock()
        mock_choice.message.content = None
        mock_choice.message.role = "assistant"
        mock_choice.message.function_call = mock_function_call
        mock_choice.finish_reason = "function_call"
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 15
        mock_response.usage.completion_tokens = 10
        mock_response.usage.total_tokens = 25
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create client
        client = OpenAIClient(api_key="test_key")
        client.client = mock_client
        
        # Test function call
        functions = [{"name": "get_account_balance", "parameters": {}}]
        result = await client.function_call(
            user_message="What's my balance?",
            functions=functions
        )
        
        assert "function_call" in result
        assert result["function_call"]["name"] == "get_account_balance"
    
    def test_usage_stats(self):
        """Test usage statistics tracking"""
        client = OpenAIClient(api_key="test_key")
        client.total_prompt_tokens = 1000
        client.total_completion_tokens = 500
        client.total_requests = 10
        
        stats = client.get_usage_stats()
        
        assert stats["total_requests"] == 10
        assert stats["total_prompt_tokens"] == 1000
        assert stats["total_completion_tokens"] == 500
        assert stats["total_tokens"] == 1500
        assert "estimated_cost_usd" in stats


class TestAnyaAgent:
    """Test Anya AI agent (mocked)"""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock OpenAI client"""
        client = Mock()
        client.chat_with_context = AsyncMock(return_value={
            "content": "I can help you with that!",
            "role": "assistant",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20}
        })
        return client
    
    @pytest.fixture
    def agent(self, mock_client):
        """Create Anya agent with mock client"""
        agent = AnyaAgent()
        agent.client = mock_client
        return agent
    
    @pytest.mark.asyncio
    async def test_chat_without_tools(self, agent, mock_client):
        """Test basic chat without tool calling"""
        response = await agent.chat(
            user_id="user_123",
            message="Hello!",
            tenant_id="tenant_1",
            use_tools=False
        )
        
        assert "message" in response
        assert response["message"] == "I can help you with that!"
        assert "usage" in response
        assert "timestamp" in response
    
    @pytest.mark.asyncio
    async def test_chat_with_function_call(self, agent):
        """Test chat with function calling"""
        # Mock function call response
        agent.client.chat_with_context = AsyncMock(side_effect=[
            {
                "content": None,
                "role": "assistant",
                "function_call": {
                    "name": "get_account_balance",
                    "arguments": {"account_id": "acc_123"}
                },
                "usage": {}
            },
            {
                "content": "Your account balance is $10,000.",
                "role": "assistant",
                "usage": {}
            }
        ])
        
        response = await agent.chat(
            user_id="user_123",
            message="What's my balance?",
            tenant_id="tenant_1",
            use_tools=True
        )
        
        assert "message" in response
        assert "tool_calls" in response
        assert len(response["tool_calls"]) == 1
    
    @pytest.mark.asyncio
    async def test_execute_task(self, agent, mock_client):
        """Test task execution"""
        response = await agent.execute_task(
            task="Check account balance for account 123",
            tenant_id="tenant_1",
            context={"account_id": "123"}
        )
        
        assert "message" in response
    
    def test_conversation_history(self, agent):
        """Test conversation history management"""
        # Get history (should be empty)
        history = agent.get_conversation_history("user_123", "tenant_1")
        assert len(history) == 0
        
        # Clear conversation
        agent.clear_conversation("user_123", "tenant_1")


class TestDomainAgents:
    """Test domain-specific agents"""
    
    def test_accounts_agent(self):
        """Test accounts agent creation"""
        agent = AnyaAccountsAgent()
        
        assert agent.domain == "Accounts"
        assert "account" in agent.domain_prompt.lower()
    
    def test_lending_agent(self):
        """Test lending agent creation"""
        agent = AnyaLendingAgent()
        
        assert agent.domain == "Lending"
        assert "loan" in agent.domain_prompt.lower()
    
    def test_security_agent(self):
        """Test security agent creation"""
        agent = AnyaSecurityAgent()
        
        assert agent.domain == "Security"
        assert "fraud" in agent.domain_prompt.lower()
