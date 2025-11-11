"""
UltraCore Assistants - Persistent Banking Relationships
Long-term customer engagement with memory
"""

from openai import OpenAI
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class PersonalBankingAssistant:
    """Personal banking assistant with long-term memory"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.assistants = {}
        self.threads = {}
        
    async def create_customer_assistant(
        self,
        customer_id: str,
        customer_profile: Dict[str, Any]
    ) -> str:
        """Create personalized assistant for customer"""
        
        # Create assistant with customer context
        assistant = self.client.beta.assistants.create(
            name=f"Personal Banker for {customer_profile.get('name', customer_id)}",
            instructions=f"""You are a personal banking assistant for an Australian customer.
            
Customer Profile:
- Name: {customer_profile.get('name')}
- Location: {customer_profile.get('location', 'Australia')}
- Account type: {customer_profile.get('account_type', 'Personal')}
- Banking preferences: {customer_profile.get('preferences', 'Standard')}
- Primary goals: {customer_profile.get('goals', 'Savings and budgeting')}

You remember all previous conversations and help with:
1. Account management and payments
2. Budgeting and savings goals
3. Investment advice (general only)
4. Australian tax optimization
5. Super (retirement) planning

Always use Australian banking terminology and amounts in AUD.
Remember customer's transaction patterns and preferences.""",
            
            tools=[
                {"type": "code_interpreter"},
                {"type": "retrieval"},
                {
                    "type": "function",
                    "function": {
                        "name": "check_balance",
                        "description": "Check account balance",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "account": {"type": "string"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "make_payment",
                        "description": "Process a payment",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "amount": {"type": "number"},
                                "recipient": {"type": "string"},
                                "method": {"type": "string"}
                            }
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "analyze_spending",
                        "description": "Analyze spending patterns",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "period": {"type": "string"},
                                "category": {"type": "string"}
                            }
                        }
                    }
                }
            ],
            model="gpt-4-turbo-preview"
        )
        
        self.assistants[customer_id] = assistant.id
        
        # Create thread for conversation
        thread = self.client.beta.threads.create()
        self.threads[customer_id] = thread.id
        
        return assistant.id
    
    async def continue_conversation(
        self,
        customer_id: str,
        message: str
    ) -> str:
        """Continue conversation with customer's assistant"""
        
        # Get or create assistant
        if customer_id not in self.assistants:
            await self.create_customer_assistant(customer_id, {})
        
        assistant_id = self.assistants[customer_id]
        thread_id = self.threads[customer_id]
        
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Run assistant
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress"]:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        # Get response
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        
        return messages.data[0].content[0].text.value
    
    async def get_conversation_summary(
        self,
        customer_id: str,
        period: str = "month"
    ) -> str:
        """Get summary of customer interactions"""
        
        thread_id = self.threads.get(customer_id)
        if not thread_id:
            return "No conversation history found"
        
        # Get all messages
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=100
        )
        
        # Create summary
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content[0].text.value}"
            for msg in messages.data
        ])
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "Summarize this banking conversation, highlighting key transactions, advice given, and customer goals."
                },
                {
                    "role": "user",
                    "content": conversation_text
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    async def proactive_insights(
        self,
        customer_id: str
    ) -> List[str]:
        """Generate proactive insights for customer"""
        
        # Get customer context
        thread_id = self.threads.get(customer_id)
        
        # Generate insights
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """Generate 3 proactive banking insights for this Australian customer.
                    Consider: saving opportunities, better account options, tax tips, super optimization."""
                },
                {
                    "role": "user",
                    "content": f"Customer {customer_id} banking patterns"
                }
            ],
            max_tokens=500
        )
        
        # Parse insights
        insights_text = response.choices[0].message.content
        insights = insights_text.split('\n')
        
        return [insight for insight in insights if insight.strip()]


class BusinessBankingAssistant:
    """Specialized assistant for Australian businesses"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        
    async def create_business_assistant(
        self,
        business_profile: Dict[str, Any]
    ) -> str:
        """Create assistant for business banking"""
        
        assistant = self.client.beta.assistants.create(
            name=f"Business Banker for {business_profile.get('name')}",
            instructions=f"""You are a business banking specialist for Australian businesses.
            
Business Profile:
- ABN: {business_profile.get('abn')}
- Industry: {business_profile.get('industry')}
- Size: {business_profile.get('size', 'SME')}
- Annual revenue: ${business_profile.get('revenue', 'N/A')}

Expertise:
1. Business loans and overdrafts
2. Merchant facilities and EFTPOS
3. Foreign exchange and international payments
4. BAS and GST management
5. Payroll and superannuation obligations
6. Cash flow management

Always consider Australian business regulations, ATO requirements, and Fair Work obligations.""",
            
            tools=[
                {"type": "code_interpreter"},
                {"type": "retrieval"}
            ],
            model="gpt-4-turbo-preview"
        )
        
        return assistant.id
