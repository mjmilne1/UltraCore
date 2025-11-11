import os

# Read API key directly from .env file (bypass dotenv caching)
def get_api_key():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'OPENAI_API_KEY=' in line:
                    return line.split('=')[1].strip()
    except:
        return os.getenv('OPENAI_API_KEY', '')
    return ''

# Set the key
OPENAI_API_KEY = get_api_key()

"""
UltraCore OpenAI Payment System
Complete payment processing with GPT-4
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass
from openai import OpenAI

# FIX: Read API key directly from .env file
def get_api_key_from_file():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if 'OPENAI_API_KEY=' in line:
                    return line.split('=')[1].strip()
    except:
        pass
    return os.getenv("OPENAI_API_KEY", "")

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """System configuration"""
    # OpenAI settings - READ DIRECTLY FROM FILE
    api_key: str = None
    model: str = "gpt-3.5-turbo"  # Using cheaper model
    embedding_model: str = "text-embedding-3-small"
    temperature: float = 0.3
    max_tokens: int = 2000
    
    # Payment settings
    max_payment_amount: Decimal = Decimal("100000")
    require_2fa_above: Decimal = Decimal("10000")
    daily_limit: Decimal = Decimal("50000")
    
    # System settings
    debug: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        # Force read API key from file
        if not self.api_key:
            self.api_key = get_api_key_from_file()

# ============================================================================
# PAYMENT MODELS
# ============================================================================

class PaymentType(Enum):
    """Payment types"""
    TRANSFER = "transfer"
    BILL = "bill"
    PAYID = "payid"
    INTERNATIONAL = "international"

class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Payment:
    """Payment record"""
    id: str
    type: PaymentType
    amount: Decimal
    currency: str = "AUD"
    from_account: str = ""
    to_destination: str = ""
    description: str = ""
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = None
    completed_at: datetime = None
    metadata: Dict = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.metadata:
            self.metadata = {}
        if not self.id:
            self.id = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"

# ============================================================================
# OPENAI FUNCTIONS
# ============================================================================

class PaymentFunctions:
    """OpenAI function definitions"""
    
    @staticmethod
    def get_tools():
        return [
            {
                "type": "function",
                "function": {
                    "name": "process_payment",
                    "description": "Process a payment transaction",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "number",
                                "description": "Payment amount in AUD"
                            },
                            "recipient": {
                                "type": "string",
                                "description": "Recipient (account, PayID, email, mobile)"
                            },
                            "payment_type": {
                                "type": "string",
                                "enum": ["transfer", "bill", "payid", "international"],
                                "description": "Type of payment"
                            },
                            "description": {
                                "type": "string",
                                "description": "Payment description"
                            }
                        },
                        "required": ["amount", "recipient"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_balance",
                    "description": "Check account balance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account": {
                                "type": "string",
                                "description": "Account number or 'all' for all accounts"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_payment_status",
                    "description": "Get status of a payment",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "payment_id": {
                                "type": "string",
                                "description": "Payment ID to check"
                            }
                        },
                        "required": ["payment_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_risk",
                    "description": "Analyze payment risk",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {
                                "type": "number",
                                "description": "Payment amount"
                            },
                            "recipient": {
                                "type": "string",
                                "description": "Recipient details"
                            },
                            "payment_type": {
                                "type": "string",
                                "description": "Type of payment"
                            }
                        },
                        "required": ["amount"]
                    }
                }
            }
        ]

# ============================================================================
# PAYMENT PROCESSOR
# ============================================================================

class PaymentProcessor:
    """Core payment processing logic"""
    
    def __init__(self):
        self.payments = {}
        self.daily_total = Decimal("0")
        self.config = Config()
    
    async def process_payment(
        self,
        amount: float,
        recipient: str,
        payment_type: str = "transfer",
        description: str = ""
    ) -> Dict[str, Any]:
        """Process a payment"""
        
        amount_decimal = Decimal(str(amount))
        
        # Validate amount
        if amount_decimal <= 0:
            return {"error": "Amount must be positive"}
        
        if amount_decimal > self.config.max_payment_amount:
            return {"error": f"Amount exceeds maximum of ${self.config.max_payment_amount}"}
        
        # Check daily limit
        if self.daily_total + amount_decimal > self.config.daily_limit:
            return {"error": f"Would exceed daily limit of ${self.config.daily_limit}"}
        
        # Create payment
        payment = Payment(
            id=f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=PaymentType(payment_type.lower()),
            amount=amount_decimal,
            to_destination=recipient,
            description=description,
            status=PaymentStatus.PROCESSING
        )
        
        # Simulate processing
        await asyncio.sleep(0.5)
        
        # Mark as completed
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.now()
        
        # Store payment
        self.payments[payment.id] = payment
        self.daily_total += amount_decimal
        
        return {
            "success": True,
            "payment_id": payment.id,
            "amount": float(payment.amount),
            "recipient": payment.to_destination,
            "status": payment.status.value,
            "message": f"Payment of ${amount} to {recipient} completed successfully"
        }
    
    async def check_balance(self, account: str = "default") -> Dict[str, Any]:
        """Check account balance"""
        # Mock balances
        balances = {
            "default": {"balance": 15234.56, "available": 14234.56},
            "savings": {"balance": 45678.90, "available": 45678.90},
            "business": {"balance": 123456.78, "available": 120456.78}
        }
        
        if account == "all":
            return {"accounts": balances, "total": sum(acc["balance"] for acc in balances.values())}
        
        return balances.get(account, {"balance": 0, "available": 0})
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Get payment status"""
        if payment_id in self.payments:
            payment = self.payments[payment_id]
            return {
                "payment_id": payment.id,
                "status": payment.status.value,
                "amount": float(payment.amount),
                "created": payment.created_at.isoformat(),
                "completed": payment.completed_at.isoformat() if payment.completed_at else None
            }
        return {"error": "Payment not found"}
    
    async def analyze_risk(
        self,
        amount: float,
        recipient: str = "",
        payment_type: str = "transfer"
    ) -> Dict[str, Any]:
        """Analyze payment risk"""
        
        risk_score = 0.1  # Base score
        risk_factors = []
        
        # Amount-based risk
        if amount > 10000:
            risk_score += 0.3
            risk_factors.append("high_amount")
        
        # International risk
        if payment_type == "international":
            risk_score += 0.2
            risk_factors.append("international")
        
        # New recipient risk (mock)
        if recipient and len(recipient) > 20:
            risk_score += 0.1
            risk_factors.append("complex_recipient")
        
        risk_level = "low" if risk_score < 0.3 else ("medium" if risk_score < 0.7 else "high")
        
        return {
            "risk_score": min(risk_score, 1.0),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": "approve" if risk_score < 0.7 else "review"
        }

# ============================================================================
# OPENAI ASSISTANT
# ============================================================================

class OpenAIPaymentAssistant:
    """OpenAI-powered payment assistant"""
    
    def __init__(self):
        self.config = Config()
        self.processor = PaymentProcessor()
        self.tools = PaymentFunctions.get_tools()
        
        # Initialize OpenAI client
        if self.config.api_key:
            self.client = OpenAI(api_key=self.config.api_key)
        else:
            self.client = None
            print("?? OpenAI API key not configured")
        
        # Conversation history
        self.messages = []
        
        # System prompt
        self.system_prompt = """You are an advanced AI payment assistant for UltraCore Banking.

You help users with:
- Processing payments and transfers
- Checking balances and transaction status
- Analyzing payment risks
- Providing payment recommendations

Available payment methods:
- Standard transfers (BSB/Account)
- PayID (mobile, email)
- BPAY bill payments
- International transfers

Security features:
- Risk analysis for all payments
- Daily limits and transaction limits
- Two-factor authentication for high-value payments

Always:
- Confirm payment details before processing
- Explain any risks or concerns
- Suggest the most efficient payment method
- Maintain professional and friendly tone
- Format currency amounts properly (e.g., $1,234.56)

Never process a payment without clear confirmation of amount and recipient."""
    
    async def chat(self, user_message: str) -> str:
        """Process user message and return response"""
        
        if not self.client:
            return "? OpenAI API key not configured. Please add your key to the .env file."
        
        try:
            # Add user message
            self.messages.append({"role": "user", "content": user_message})
            
            # Prepare messages with system prompt
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.messages[-10:]  # Keep last 10 messages for context
            ]
            
            # Call OpenAI
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.config.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            assistant_message = response.choices[0].message
            
            # Handle function calls
            if assistant_message.tool_calls:
                tool_call = assistant_message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute function
                result = await self._execute_function(function_name, function_args)
                
                # Add to messages
                self.messages.append(assistant_message)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
                
                # Get final response
                final_messages = [
                    {"role": "system", "content": self.system_prompt},
                    *self.messages[-10:]
                ]
                
                final_response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.config.model,
                    messages=final_messages,
                    temperature=self.config.temperature
                )
                
                final_content = final_response.choices[0].message.content
                self.messages.append({"role": "assistant", "content": final_content})
                return final_content
            
            else:
                # Regular response
                content = assistant_message.content
                self.messages.append({"role": "assistant", "content": content})
                return content
                
        except Exception as e:
            return f"? Error: {str(e)}"
    
    async def _execute_function(self, name: str, args: Dict) -> Dict:
        """Execute function called by OpenAI"""
        
        if name == "process_payment":
            return await self.processor.process_payment(**args)
        elif name == "check_balance":
            return await self.processor.check_balance(**args)
        elif name == "get_payment_status":
            return await self.processor.get_payment_status(**args)
        elif name == "analyze_risk":
            return await self.processor.analyze_risk(**args)
        else:
            return {"error": f"Unknown function: {name}"}

# ============================================================================
# MAIN INTERFACE
# ============================================================================

class UltraCorePaymentSystem:
    """Main payment system interface"""
    
    def __init__(self):
        self.assistant = OpenAIPaymentAssistant()
        print("?? UltraCore Payment System initialized")
        if self.assistant.client:
            print(f"? OpenAI connected (Model: {self.assistant.config.model})")
        else:
            print("?? OpenAI not connected - check API key")
    
    async def start_interactive_session(self):
        """Start interactive chat session"""
        print("\n" + "="*60)
        print("?? ULTRACORE PAYMENT ASSISTANT")
        print("="*60)
        print("Type 'help' for commands, 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'exit':
                    print("?? Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print("""
Available commands:
- Send money: "Send $100 to John at 0412345678"
- Pay bills: "Pay my electricity bill for $250"
- Check balance: "What's my balance?"
- Check payment: "Check payment PAY20240101123456"
- Risk analysis: "Is it safe to send $10000?"
- exit: Quit the system
                    """)
                else:
                    response = await self.assistant.chat(user_input)
                    print(f"\n?? Assistant: {response}\n")
                    
            except KeyboardInterrupt:
                print("\n?? Goodbye!")
                break
            except Exception as e:
                print(f"? Error: {e}")
    
    async def process_single_request(self, request: str) -> str:
        """Process a single payment request"""
        return await self.assistant.chat(request)

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_system():
    """Test the payment system"""
    print("\n" + "="*60)
    print("?? TESTING ULTRACORE PAYMENT SYSTEM")
    print("="*60)
    
    system = UltraCorePaymentSystem()
    
    # Test requests
    test_requests = [
        "Hello! What can you help me with?",
        "Check my balance",
        "Send $250 to Sarah at 0412345678 for dinner",
        "Is it risky to send $50000 to a new recipient?",
        "Pay my internet bill for $89.99"
    ]
    
    for request in test_requests:
        print(f"\n?? User: {request}")
        response = await system.process_single_request(request)
        print(f"?? Assistant: {response}")
    
    print("\n" + "="*60)
    print("? TEST COMPLETE")
    print("="*60)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        asyncio.run(test_system())
    else:
        # Run interactive session
        system = UltraCorePaymentSystem()
        asyncio.run(system.start_interactive_session())


