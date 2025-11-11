"""
OpenAI Payment Assistant
"""
import openai
import json
import asyncio
from typing import Dict, List, Any
from decimal import Decimal
from .openai_config import settings

class PaymentFunctions:
    @staticmethod
    def get_functions() -> List[Dict[str, Any]]:
        return [
            {
                "name": "send_payment",
                "description": "Send a payment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "recipient": {"type": "string"}
                    },
                    "required": ["amount", "recipient"]
                }
            }
        ]

class OpenAIPaymentAssistant:
    def __init__(self, payment_orchestrator):
        self.orchestrator = payment_orchestrator
        self.functions = PaymentFunctions.get_functions()
        self.system_prompt = "You are a payment assistant."
        
        if settings.api_key:
            openai.api_key = settings.api_key
    
    async def process_message(self, message: str) -> str:
        if not settings.api_key:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY."
        
        try:
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=settings.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ],
                functions=self.functions,
                function_call="auto",
                temperature=settings.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
