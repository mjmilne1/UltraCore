"""
Anya API - Customer Conversational Interface
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

from ultracore.anya.core import get_anya, Intent

router = APIRouter()


class ChatRequest(BaseModel):
    customer_id: str
    message: str


class ChatResponse(BaseModel):
    message: str
    action: str
    data: Optional[dict] = None


@router.post('/chat')
async def chat(request: ChatRequest) -> ChatResponse:
    '''
    Chat with Anya
    
    Customer sends natural language message, Anya responds intelligently
    '''
    anya = get_anya()
    
    response = await anya.process_message(
        customer_id=request.customer_id,
        message=request.message
    )
    
    return ChatResponse(**response)


@router.get('/conversation/{customer_id}')
async def get_conversation_history(customer_id: str):
    '''Get conversation history for customer'''
    anya = get_anya()
    context = anya.get_context(customer_id)
    
    return {
        'customer_id': customer_id,
        'messages': context.messages,
        'current_intent': context.current_intent.value if context.current_intent else None
    }


@router.post('/execute/{customer_id}')
async def execute_action(customer_id: str, action: str, params: dict):
    '''
    Execute action confirmed by customer
    
    After Anya collects info and gets confirmation, execute the actual operation
    '''
    anya = get_anya()
    
    if action == 'transfer_money':
        return await _execute_transfer(customer_id, params)
    
    elif action == 'apply_loan':
        return await _execute_loan_application(customer_id, params)
    
    elif action == 'issue_card':
        return await _execute_card_issuance(customer_id, params)
    
    elif action == 'place_order':
        return await _execute_investment_order(customer_id, params)
    
    elif action == 'submit_claim':
        return await _execute_insurance_claim(customer_id, params)
    
    else:
        raise HTTPException(status_code=400, detail=f'Unknown action: {action}')


async def _execute_transfer(customer_id: str, params: dict):
    '''Execute money transfer'''
    from ultracore.domains.payment.complete_aggregate import CompletePaymentAggregate, PaymentType
    from decimal import Decimal
    import uuid
    
    payment_id = f'PAY-{str(uuid.uuid4())[:8]}'
    payment = CompletePaymentAggregate(payment_id)
    
    await payment.initiate_payment(
        from_account_id=params['from_account_id'],
        to_account_id=params['to_account_id'],
        amount=Decimal(str(params['amount'])),
        payment_type=PaymentType.INTERNAL_TRANSFER,
        description='Transfer via Anya',
        reference=customer_id
    )
    
    # Fraud check
    fraud_approved = await payment.fraud_check()
    
    if not fraud_approved:
        return {
            'success': False,
            'message': '⚠️ This transfer has been flagged for review. Our team will contact you shortly.',
            'payment_id': payment_id,
            'status': 'FRAUD_HOLD'
        }
    
    # Process
    await payment.process_payment()
    await payment.clear_payment()
    await payment.settle_payment()
    
    return {
        'success': True,
        'message': f"✅ Transfer complete!  has been sent.",
        'payment_id': payment_id,
        'status': 'SETTLED'
    }


async def _execute_loan_application(customer_id: str, params: dict):
    '''Execute loan application'''
    from ultracore.domains.loan.origination import LoanOrigination
    from decimal import Decimal
    import uuid
    
    loan_id = f'LN-{str(uuid.uuid4())[:8]}'
    loan = LoanOrigination(loan_id)
    
    await loan.apply(
        customer_id=customer_id,
        amount=Decimal(str(params['amount'])),
        purpose=params.get('purpose', 'Personal'),
        term_months=params.get('term_months', 36)
    )
    
    # AI underwriting
    await loan.underwrite()
    
    if loan.status.value == 'APPROVED':
        return {
            'success': True,
            'message': f"🎉 Congratulations! Your loan application for  has been approved!\n\n" +
                      f"Interest Rate: {loan.interest_rate}%\n" +
                      f"Monthly Payment: \n" +
                      f"Term: {params.get('term_months', 36)} months",
            'loan_id': loan_id,
            'status': 'APPROVED'
        }
    else:
        return {
            'success': False,
            'message': "We're unable to approve your loan application at this time. Please contact us to discuss alternatives.",
            'loan_id': loan_id,
            'status': 'REJECTED'
        }


async def _execute_card_issuance(customer_id: str, params: dict):
    '''Execute card issuance'''
    from ultracore.domains.cards.complete_aggregate import CompleteCardAggregate, CardType
    from decimal import Decimal
    import uuid
    
    card_id = f'CRD-{str(uuid.uuid4())[:8]}'
    card = CompleteCardAggregate(card_id)
    
    card_type = CardType[params['card_type'].upper()]
    credit_limit = params.get('credit_limit')
    
    await card.issue_card(
        account_id=params['account_id'],
        card_type=card_type,
        credit_limit=Decimal(str(credit_limit)) if credit_limit else None
    )
    
    await card.activate_card()
    
    return {
        'success': True,
        'message': f"🎉 Your {card_type.value.lower()} card has been issued!\n\n" +
                  f"Card ending in: {card.card_number_last4}\n" +
                  f"Expires: {card.expiry_date}\n\n" +
                  "Your physical card will arrive in 5-7 business days. You can use it digitally right away!",
        'card_id': card_id,
        'card_last4': card.card_number_last4
    }


async def _execute_investment_order(customer_id: str, params: dict):
    '''Execute investment order'''
    from ultracore.domains.investment.complete_aggregate import CompleteInvestmentAggregate, OrderSide, OrderType
    
    portfolio_id = params['portfolio_id']
    portfolio = CompleteInvestmentAggregate(portfolio_id)
    await portfolio.load_from_events()
    
    order_id = await portfolio.place_order(
        symbol=params['symbol'],
        side=OrderSide[params['side'].upper()],
        quantity=params['quantity'],
        order_type=OrderType.MARKET
    )
    
    return {
        'success': True,
        'message': f"✅ Order placed! {params['side']} {params['quantity']} shares of {params['symbol']}",
        'order_id': order_id
    }


async def _execute_insurance_claim(customer_id: str, params: dict):
    '''Execute insurance claim submission'''
    from ultracore.domains.insurance.complete_aggregate import CompleteInsuranceAggregate
    from decimal import Decimal
    
    policy_id = params['policy_id']
    policy = CompleteInsuranceAggregate(policy_id)
    await policy.load_from_events()
    
    claim_id = await policy.submit_claim(
        claim_amount=Decimal(str(params['claim_amount'])),
        incident_date=params['incident_date'],
        description=params['description'],
        supporting_docs=params.get('supporting_docs', [])
    )
    
    return {
        'success': True,
        'message': f"✅ Your claim has been submitted!\n\n" +
                  f"Claim ID: {claim_id}\n" +
                  f"Amount: \n\n" +
                  "We'll review your claim and get back to you within 2-3 business days.",
        'claim_id': claim_id
    }


# WebSocket for real-time chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, customer_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[customer_id] = websocket
    
    def disconnect(self, customer_id: str):
        if customer_id in self.active_connections:
            del self.active_connections[customer_id]
    
    async def send_message(self, customer_id: str, message: dict):
        if customer_id in self.active_connections:
            await self.active_connections[customer_id].send_json(message)


manager = ConnectionManager()


@router.websocket('/ws/{customer_id}')
async def websocket_chat(websocket: WebSocket, customer_id: str):
    '''
    WebSocket endpoint for real-time chat with Anya
    
    Provides instant responses and better UX
    '''
    await manager.connect(customer_id, websocket)
    anya = get_anya()
    
    try:
        # Send welcome message
        await websocket.send_json({
            'type': 'welcome',
            'message': "👋 Hi! I'm Anya, your personal banking assistant. How can I help you today?"
        })
        
        while True:
            # Receive message from customer
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process with Anya
            response = await anya.process_message(
                customer_id=customer_id,
                message=message_data['message']
            )
            
            # Send response
            await websocket.send_json({
                'type': 'message',
                'response': response
            })
            
    except WebSocketDisconnect:
        manager.disconnect(customer_id)


@router.get('/suggestions/{customer_id}')
async def get_suggestions(customer_id: str):
    '''
    Get personalized suggestions for customer
    
    Proactive recommendations based on customer data
    '''
    # In production: analyze customer behavior, financial health
    
    suggestions = [
        {
            'type': 'savings_goal',
            'message': "💡 You're  away from your ,000 savings goal! Would you like to set up an automatic transfer?",
            'action': 'setup_auto_transfer'
        },
        {
            'type': 'investment',
            'message': "📈 Based on your risk profile, you might consider diversifying into ETFs. Want to learn more?",
            'action': 'learn_about_etfs'
        },
        {
            'type': 'loan_payoff',
            'message': "🎯 You could save  in interest by increasing your loan payment by /month. Interested?",
            'action': 'optimize_loan'
        }
    ]
    
    return {
        'customer_id': customer_id,
        'suggestions': suggestions
    }


@router.post('/feedback/{customer_id}')
async def submit_feedback(customer_id: str, rating: int, comment: str):
    '''Submit feedback on Anya interaction'''
    return {
        'success': True,
        'message': 'Thank you for your feedback!'
    }
