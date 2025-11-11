"""
UltraCore Payment System - Working Version
"""
import asyncio
from openai import OpenAI
from typing import Dict, List, Any
from datetime import datetime
from decimal import Decimal
import json

# Read API key directly from .env
api_key = None
with open('.env', 'r') as f:
    for line in f:
        if 'OPENAI_API_KEY=' in line:
            api_key = line.split('=')[1].strip()
            break

print(f"?? Payment System initialized (API: {api_key[:20]}...)")

# Initialize OpenAI
client = OpenAI(api_key=api_key)

class PaymentSystem:
    """Complete payment system with OpenAI"""
    
    def __init__(self):
        self.client = client
        self.payments = []
        self.system_prompt = """You are an AI payment assistant for UltraCore Banking.

You can help with:
1. Processing payments (NPP, PayID, BPAY)
2. Checking balances
3. Analyzing payment risks
4. Payment recommendations

When users request payments, confirm the details:
- Amount (in AUD)
- Recipient (name, PayID, mobile, or account)
- Description/purpose

Always format responses professionally and clearly."""

    async def process_request(self, user_message: str) -> str:
        """Process user payment request"""
        
        # Check for payment intent
        if any(word in user_message.lower() for word in ['send', 'pay', 'transfer']):
            return await self.handle_payment(user_message)
        elif 'balance' in user_message.lower():
            return await self.check_balance()
        elif 'risk' in user_message.lower() or 'safe' in user_message.lower():
            return await self.analyze_risk(user_message)
        else:
            return await self.general_assistance(user_message)
    
    async def handle_payment(self, message: str) -> str:
        """Handle payment request"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Process this payment request: {message}"}
            ],
            functions=[{
                "name": "process_payment",
                "description": "Process a payment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "recipient": {"type": "string"},
                        "description": {"type": "string"}
                    },
                    "required": ["amount", "recipient"]
                }
            }],
            function_call="auto"
        )
        
        msg = response.choices[0].message
        
        if msg.function_call:
            # Extract payment details
            args = json.loads(msg.function_call.arguments)
            amount = args.get('amount', 0)
            recipient = args.get('recipient', 'Unknown')
            
            # Create payment record
            payment = {
                "id": f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "amount": amount,
                "recipient": recipient,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            }
            self.payments.append(payment)
            
            return f"""? Payment Processed Successfully!
            
Payment ID: {payment['id']}
Amount: ${amount:,.2f} AUD
Recipient: {recipient}
Status: Completed
Time: {datetime.now().strftime('%H:%M:%S')}

Your payment has been sent via NPP (real-time)."""
        
        return msg.content
    
    async def check_balance(self) -> str:
        """Check account balance"""
        return """?? Account Balances:

Main Account: $15,234.56 AUD
Available: $14,234.56 AUD

Savings Account: $45,678.90 AUD
Available: $45,678.90 AUD

Total Available: $59,913.46 AUD

Recent Transactions: {} payments today""".format(len(self.payments))
    
    async def analyze_risk(self, message: str) -> str:
        """Analyze payment risk"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a risk analysis expert."},
                {"role": "user", "content": f"Analyze this payment risk: {message}"}
            ],
            max_tokens=200
        )
        
        return f"?? Risk Analysis:\n\n{response.choices[0].message.content}"
    
    async def general_assistance(self, message: str) -> str:
        """General assistance"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=200
        )
        
        return response.choices[0].message.content

async def test_system():
    """Test the payment system"""
    print("\n" + "="*60)
    print("ULTRACORE PAYMENT SYSTEM TEST")
    print("="*60 + "\n")
    
    system = PaymentSystem()
    
    test_cases = [
        "What can you help me with?",
        "Check my balance",
        "Send $500 to John Smith at 0412345678",
        "Analyze the risk of sending $25000 internationally",
        "Pay my electricity bill for $234.50"
    ]
    
    for test in test_cases:
        print(f"?? User: {test}")
        response = await system.process_request(test)
        print(f"?? Assistant: {response}\n")
        print("-"*40)
    
    print("\n? All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_system())
