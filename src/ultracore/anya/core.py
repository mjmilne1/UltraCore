"""
Anya - Customer AI Interface
Primary customer interaction layer for UltraCore
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import re


class Intent(str, Enum):
    # Account operations
    CHECK_BALANCE = 'CHECK_BALANCE'
    VIEW_TRANSACTIONS = 'VIEW_TRANSACTIONS'
    OPEN_ACCOUNT = 'OPEN_ACCOUNT'
    
    # Payment operations
    TRANSFER_MONEY = 'TRANSFER_MONEY'
    PAY_BILL = 'PAY_BILL'
    
    # Card operations
    REQUEST_CARD = 'REQUEST_CARD'
    BLOCK_CARD = 'BLOCK_CARD'
    VIEW_CARD_TRANSACTIONS = 'VIEW_CARD_TRANSACTIONS'
    
    # Loan operations
    APPLY_LOAN = 'APPLY_LOAN'
    CHECK_LOAN_STATUS = 'CHECK_LOAN_STATUS'
    MAKE_LOAN_PAYMENT = 'MAKE_LOAN_PAYMENT'
    
    # Investment operations
    VIEW_PORTFOLIO = 'VIEW_PORTFOLIO'
    BUY_STOCK = 'BUY_STOCK'
    SELL_STOCK = 'SELL_STOCK'
    
    # Insurance operations
    GET_INSURANCE_QUOTE = 'GET_INSURANCE_QUOTE'
    SUBMIT_CLAIM = 'SUBMIT_CLAIM'
    CHECK_CLAIM_STATUS = 'CHECK_CLAIM_STATUS'
    
    # General
    GENERAL_QUESTION = 'GENERAL_QUESTION'
    HELP = 'HELP'


class ConversationContext:
    """Maintains conversation state for customer"""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.messages: List[Dict] = []
        self.current_intent: Optional[Intent] = None
        self.collected_params: Dict[str, Any] = {}
        self.pending_confirmation: Optional[Dict] = None
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def set_intent(self, intent: Intent):
        """Set current customer intent"""
        self.current_intent = intent
        self.collected_params = {}
    
    def add_param(self, key: str, value: Any):
        """Collect parameter for intent"""
        self.collected_params[key] = value
    
    def is_complete(self) -> bool:
        """Check if all required params collected"""
        required = INTENT_PARAMS.get(self.current_intent, [])
        return all(p in self.collected_params for p in required)


# Required parameters for each intent
INTENT_PARAMS = {
    Intent.TRANSFER_MONEY: ['to_account', 'amount'],
    Intent.APPLY_LOAN: ['loan_amount', 'loan_purpose'],
    Intent.BUY_STOCK: ['symbol', 'quantity'],
    Intent.SUBMIT_CLAIM: ['claim_amount', 'incident_date', 'description']
}


class IntentRecognizer:
    """Recognizes customer intent from natural language"""
    
    PATTERNS = {
        Intent.CHECK_BALANCE: [
            r'check.*balance',
            r'how much.*account',
            r'account balance',
            r'show.*balance'
        ],
        Intent.TRANSFER_MONEY: [
            r'transfer.*money',
            r'send.*\True\d+',
            r'pay.*someone',
            r'transfer.*\True\d+'
        ],
        Intent.APPLY_LOAN: [
            r'apply.*loan',
            r'need.*loan',
            r'get.*loan',
            r'loan application'
        ],
        Intent.REQUEST_CARD: [
            r'get.*card',
            r'apply.*card',
            r'new card',
            r'credit card'
        ],
        Intent.VIEW_PORTFOLIO: [
            r'portfolio',
            r'investments',
            r'stocks',
            r'my holdings'
        ]
    }
    
    @classmethod
    def recognize(cls, message: str) -> Intent:
        """Recognize intent from customer message"""
        message_lower = message.lower()
        
        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return Intent.GENERAL_QUESTION
    
    @classmethod
    def extract_entities(cls, message: str, intent: Intent) -> Dict:
        """Extract entities (amounts, dates, etc) from message"""
        entities = {}
        
        # Extract dollar amounts
        amounts = re.findall(r'\True([\d,]+\.?\d*)', message)
        if amounts and intent == Intent.TRANSFER_MONEY:
            entities['amount'] = float(amounts[0].replace(',', ''))
        
        # Extract account references
        if 'account' in message.lower():
            # Extract account IDs or names
            pass
        
        return entities


class Anya:
    """
    Anya - Customer AI Assistant
    
    Natural language interface to all UltraCore capabilities
    """
    
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_context(self, customer_id: str) -> ConversationContext:
        """Get or create conversation context"""
        if customer_id not in self.contexts:
            self.contexts[customer_id] = ConversationContext(customer_id)
        return self.contexts[customer_id]
    
    async def process_message(
        self,
        customer_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Process customer message
        
        Returns response with actions to take
        """
        context = self.get_context(customer_id)
        context.add_message('user', message)
        
        # Recognize intent
        intent = IntentRecognizer.recognize(message)
        
        # Extract entities
        entities = IntentRecognizer.extract_entities(message, intent)
        
        # Handle intent
        if intent == Intent.CHECK_BALANCE:
            response = await self._handle_check_balance(customer_id)
        
        elif intent == Intent.TRANSFER_MONEY:
            response = await self._handle_transfer(customer_id, entities, context)
        
        elif intent == Intent.APPLY_LOAN:
            response = await self._handle_loan_application(customer_id, entities, context)
        
        elif intent == Intent.VIEW_PORTFOLIO:
            response = await self._handle_view_portfolio(customer_id)
        
        elif intent == Intent.REQUEST_CARD:
            response = await self._handle_card_request(customer_id)
        
        else:
            response = await self._handle_general_question(customer_id, message)
        
        context.add_message('assistant', response['message'])
        
        return response
    
    async def _handle_check_balance(self, customer_id: str) -> Dict:
        """Handle balance inquiry"""
        # Get customer's accounts
        from ultracore.domains.account.complete_aggregate import CompleteAccountAggregate
        
        # In production: query customer's accounts from DB
        # For now, simulate
        
        return {
            'message': "I can help you check your balance! You have:\n\n" +
                      "💰 Checking Account (ACC-12345): ,432.18\n" +
                      "💎 Savings Account (ACC-67890): ,850.00\n\n" +
                      "Is there anything else you'd like to know?",
            'action': 'display_balances',
            'data': {
                'accounts': [
                    {'id': 'ACC-12345', 'type': 'CHECKING', 'balance': 5432.18},
                    {'id': 'ACC-67890', 'type': 'SAVINGS', 'balance': 12850.00}
                ]
            }
        }
    
    async def _handle_transfer(
        self,
        customer_id: str,
        entities: Dict,
        context: ConversationContext
    ) -> Dict:
        """Handle money transfer"""
        
        # Check if we have all required info
        if 'amount' not in entities:
            return {
                'message': "I can help you transfer money! How much would you like to transfer?",
                'action': 'collect_param',
                'param': 'amount'
            }
        
        amount = entities['amount']
        
        # Confirm before executing
        return {
            'message': f"I'll transfer  for you. " +
                      "Which account would you like to transfer from?\n\n" +
                      "1. Checking (ACC-12345) - ,432.18\n" +
                      "2. Savings (ACC-67890) - ,850.00",
            'action': 'confirm_transfer',
            'data': {
                'amount': amount,
                'needs_confirmation': True
            }
        }
    
    async def _handle_loan_application(
        self,
        customer_id: str,
        entities: Dict,
        context: ConversationContext
    ) -> Dict:
        """Handle loan application"""
        
        return {
            'message': "I'd be happy to help you apply for a loan! 🏦\n\n" +
                      "To get started, I need a few details:\n" +
                      "1. How much would you like to borrow?\n" +
                      "2. What's the purpose of the loan?\n" +
                      "3. How long would you like to repay it?\n\n" +
                      "Based on your profile, you may qualify for up to ,000 " +
                      "at competitive rates. Let me know the amount and we'll proceed!",
            'action': 'start_loan_application',
            'data': {
                'max_eligible': 50000,
                'estimated_rate': 6.5
            }
        }
    
    async def _handle_view_portfolio(self, customer_id: str) -> Dict:
        """Handle portfolio inquiry"""
        
        return {
            'message': "Here's your investment portfolio summary:\n\n" +
                      "📊 Total Value: ,340.50 (+2.3% today)\n\n" +
                      "Holdings:\n" +
                      "• AAPL - 10 shares - ,850.00\n" +
                      "• GOOGL - 5 shares - .00\n" +
                      "• MSFT - 15 shares - ,250.00\n" +
                      "• ETF (VAS) - 100 units - ,500.00\n" +
                      "• Cash - ,865.50\n\n" +
                      "Would you like to make any trades?",
            'action': 'display_portfolio',
            'data': {
                'total_value': 25340.50,
                'daily_change': 2.3,
                'holdings': [
                    {'symbol': 'AAPL', 'quantity': 10, 'value': 1850.00},
                    {'symbol': 'GOOGL', 'quantity': 5, 'value': 875.00}
                ]
            }
        }
    
    async def _handle_card_request(self, customer_id: str) -> Dict:
        """Handle card request"""
        
        return {
            'message': "I can help you get a new card! 💳\n\n" +
                      "We offer:\n" +
                      "1. **Debit Card** - Instant access to your checking account\n" +
                      "2. **Credit Card** - Up to ,000 credit limit\n" +
                      "3. **Prepaid Card** - Load funds as needed\n\n" +
                      "Which type interests you?",
            'action': 'card_selection',
            'data': {
                'card_types': ['debit', 'credit', 'prepaid']
            }
        }
    
    async def _handle_general_question(
        self,
        customer_id: str,
        message: str
    ) -> Dict:
        """Handle general questions with AI"""
        
        # In production: call Claude API for intelligent responses
        
        return {
            'message': "I'm Anya, your personal banking assistant! I can help you with:\n\n" +
                      "💰 Account management\n" +
                      "💸 Payments and transfers\n" +
                      "💳 Cards\n" +
                      "🏦 Loans\n" +
                      "📈 Investments\n" +
                      "🛡️ Insurance\n\n" +
                      "What would you like to do today?",
            'action': 'show_menu'
        }


# Global Anya instance
_anya: Optional[Anya] = None


def get_anya() -> Anya:
    global _anya
    if _anya is None:
        _anya = Anya()
    return _anya
