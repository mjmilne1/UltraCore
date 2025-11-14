"""
OpenAI Client Wrapper

Real AI integration using OpenAI API with streaming, function calling, and error handling.
"""

import os
from typing import Dict, List, Optional, AsyncIterator, Any
from datetime import datetime
import json
import asyncio

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None


class OpenAIClient:
    """
    Production-grade OpenAI client with:
    - Async streaming support
    - Function calling for MCP tools
    - Error handling and retries
    - Token usage tracking
    - Cost estimation
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1-mini",
        max_retries: int = 3
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")
        
        self.model = model
        self.max_retries = max_retries
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Token usage tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_requests = 0
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        functions: Optional[List[Dict]] = None,
        function_call: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Create a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            functions: List of function definitions for function calling
            function_call: Force function call ("auto", "none", or {"name": "function_name"})
            stream: Whether to stream the response
        
        Returns:
            Response dict with 'content', 'role', 'function_call', 'usage'
        """
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        
        if functions:
            kwargs["functions"] = functions
        
        if function_call:
            kwargs["function_call"] = function_call
        
        if stream:
            kwargs["stream"] = True
            return await self._stream_completion(**kwargs)
        
        # Non-streaming completion
        for attempt in range(self.max_retries):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                
                # Track usage
                if hasattr(response, 'usage'):
                    self.total_prompt_tokens += response.usage.prompt_tokens
                    self.total_completion_tokens += response.usage.completion_tokens
                    self.total_requests += 1
                
                # Extract response
                choice = response.choices[0]
                result = {
                    "content": choice.message.content,
                    "role": choice.message.role,
                    "finish_reason": choice.finish_reason,
                }
                
                # Add function call if present
                if hasattr(choice.message, 'function_call') and choice.message.function_call:
                    result["function_call"] = {
                        "name": choice.message.function_call.name,
                        "arguments": json.loads(choice.message.function_call.arguments)
                    }
                
                # Add usage info
                if hasattr(response, 'usage'):
                    result["usage"] = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                
                return result
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _stream_completion(self, **kwargs) -> AsyncIterator[str]:
        """Stream completion tokens"""
        stream = await self.client.chat.completions.create(**kwargs)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def chat_with_context(
        self,
        user_message: str,
        context: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat with conversation context.
        
        Args:
            user_message: User's message
            context: Previous conversation messages
            system_prompt: System prompt to set behavior
            **kwargs: Additional arguments for chat_completion
        
        Returns:
            Response dict
        """
        messages = []
        
        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add context
        messages.extend(context)
        
        # Add user message
        messages.append({"role": "user", "content": user_message})
        
        return await self.chat_completion(messages, **kwargs)
    
    async def function_call(
        self,
        user_message: str,
        functions: List[Dict],
        context: Optional[List[Dict[str, str]]] = None,
        force_function: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a function call using OpenAI function calling.
        
        Args:
            user_message: User's message
            functions: List of function definitions
            context: Previous conversation messages
            force_function: Force a specific function to be called
        
        Returns:
            Response dict with function_call
        """
        messages = context or []
        messages.append({"role": "user", "content": user_message})
        
        function_call = "auto"
        if force_function:
            function_call = {"name": force_function}
        
        return await self.chat_completion(
            messages=messages,
            functions=functions,
            function_call=function_call,
            temperature=0.0  # Lower temperature for function calls
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        return {
            "total_requests": self.total_requests,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "estimated_cost_usd": self._estimate_cost()
        }
    
    def _estimate_cost(self) -> float:
        """
        Estimate cost based on token usage.
        
        Pricing (as of Nov 2025):
        - gpt-4.1-mini: $0.15/1M input, $0.60/1M output
        - gpt-4.1-nano: $0.10/1M input, $0.40/1M output
        """
        if "mini" in self.model:
            input_cost = (self.total_prompt_tokens / 1_000_000) * 0.15
            output_cost = (self.total_completion_tokens / 1_000_000) * 0.60
        elif "nano" in self.model:
            input_cost = (self.total_prompt_tokens / 1_000_000) * 0.10
            output_cost = (self.total_completion_tokens / 1_000_000) * 0.40
        else:
            # Default to mini pricing
            input_cost = (self.total_prompt_tokens / 1_000_000) * 0.15
            output_cost = (self.total_completion_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost
    
    def reset_stats(self):
        """Reset usage statistics"""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_requests = 0


class AIClientFactory:
    """Factory for creating AI clients"""
    
    _instances: Dict[str, OpenAIClient] = {}
    
    @classmethod
    def get_client(
        cls,
        model: str = "gpt-4.1-mini",
        api_key: Optional[str] = None
    ) -> OpenAIClient:
        """
        Get or create an OpenAI client.
        
        Clients are cached per model to reuse connections.
        """
        cache_key = f"{model}:{api_key or 'default'}"
        
        if cache_key not in cls._instances:
            cls._instances[cache_key] = OpenAIClient(
                api_key=api_key,
                model=model
            )
        
        return cls._instances[cache_key]
    
    @classmethod
    def reset_all_stats(cls):
        """Reset stats for all clients"""
        for client in cls._instances.values():
            client.reset_stats()
    
    @classmethod
    def get_total_usage(cls) -> Dict[str, Any]:
        """Get total usage across all clients"""
        total_requests = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        
        for client in cls._instances.values():
            stats = client.get_usage_stats()
            total_requests += stats["total_requests"]
            total_prompt_tokens += stats["total_prompt_tokens"]
            total_completion_tokens += stats["total_completion_tokens"]
            total_cost += stats["estimated_cost_usd"]
        
        return {
            "total_requests": total_requests,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens,
            "estimated_cost_usd": total_cost
        }
