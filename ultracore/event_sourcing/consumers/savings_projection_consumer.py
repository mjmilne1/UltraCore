"""
Savings Projection Consumer
Materializes savings events into database read models
"""

from typing import Dict, Any
import logging
from decimal import Decimal
from datetime import datetime

from ultracore.event_sourcing.consumers.base_consumer import BaseEventConsumer

logger = logging.getLogger(__name__)


class SavingsProjectionConsumer(BaseEventConsumer):
    """
    Consumes savings events and projects them into PostgreSQL
    
    This implements the CQRS pattern:
    - Events are the source of truth (Kafka)
    - Projections are optimized read models (PostgreSQL)
    """
    
    def __init__(
        self,
        database_session_factory,
        bootstrap_servers: str = "localhost:9092"
    ):
        topics = [
            "ultracore.savings.accounts.lifecycle",
            "ultracore.savings.accounts.transactions",
            "ultracore.savings.interest",
            "ultracore.savings.fees",
        ]
        
        super().__init__(
            topics=topics,
            group_id="ultracore-savings-projection",
            bootstrap_servers=bootstrap_servers
        )
        
        self.db_session_factory = database_session_factory
    
    async def process_event(self, event: Dict[str, Any]) -> bool:
        """Process savings event and update projection"""
        event_type = event.get('event_type')
        
        # Route to appropriate handler
        handler = self._get_handler(event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return True  # Skip unknown events
        
        try:
            async with self.db_session_factory() as session:
                await handler(event, session)
                await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to process event {event_type}: {e}")
            return False
    
    def _get_handler(self, event_type: str):
        """Get handler for event type"""
        handlers = {
            # Account lifecycle
            "SavingsAccountOpened": self._handle_account_opened,
            "SavingsAccountApproved": self._handle_account_approved,
            "SavingsAccountActivated": self._handle_account_activated,
            "SavingsAccountClosed": self._handle_account_closed,
            "SavingsAccountFrozen": self._handle_account_frozen,
            "SavingsAccountDormant": self._handle_account_dormant,
            "SavingsAccountTFNProvided": self._handle_tfn_provided,
            
            # Transactions
            "SavingsDeposit": self._handle_deposit,
            "SavingsWithdrawal": self._handle_withdrawal,
            "SavingsTransferIn": self._handle_transfer_in,
            "SavingsTransferOut": self._handle_transfer_out,
            
            # Interest
            "InterestAccrued": self._handle_interest_accrued,
            "InterestPosted": self._handle_interest_posted,
            "BonusInterestEarned": self._handle_bonus_earned,
            "BonusInterestForfeited": self._handle_bonus_forfeited,
            "WithholdingTaxDeducted": self._handle_withholding_tax,
            
            # Fees
            "MonthlyFeeCharged": self._handle_monthly_fee,
            "FeeWaived": self._handle_fee_waived,
            "WithdrawalFeeCharged": self._handle_withdrawal_fee,
        }
        
        return handlers.get(event_type)
    
    # ========================================================================
    # Account Lifecycle Handlers
    # ========================================================================
    
    async def _handle_account_opened(self, event: Dict[str, Any], session):
        """Handle account opened event"""
        from ultracore.database.models import SavingsAccountModel
        
        data = event['event_data']
        
        account = SavingsAccountModel(
            account_id=event['aggregate_id'],
            client_id=data['client_id'],
            product_id=data['product_id'],
            tenant_id=event['tenant_id'],
            account_number=data['account_number'],
            bsb=data.get('bsb'),
            account_name=data['account_name'],
            account_type=data['account_type'],
            status='pending',
            balance=Decimal('0.00'),
            available_balance=Decimal('0.00'),
            created_at=datetime.fromisoformat(event['event_timestamp']),
            created_by=event['user_id'],
        )
        
        session.add(account)
    
    async def _handle_account_approved(self, event: Dict[str, Any], session):
        """Handle account approved event"""
        from ultracore.database.models import SavingsAccountModel
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.status = 'approved'
            account.approved_at = datetime.fromisoformat(event['event_timestamp'])
            account.approved_by = event['user_id']
    
    async def _handle_account_activated(self, event: Dict[str, Any], session):
        """Handle account activated event"""
        from ultracore.database.models import SavingsAccountModel
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.status = 'active'
            account.activated_at = datetime.fromisoformat(event['event_timestamp'])
    
    async def _handle_account_closed(self, event: Dict[str, Any], session):
        """Handle account closed event"""
        from ultracore.database.models import SavingsAccountModel
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.status = 'closed'
            account.closed_at = datetime.fromisoformat(event['event_timestamp'])
            account.closed_by = event['user_id']
    
    async def _handle_account_frozen(self, event: Dict[str, Any], session):
        """Handle account frozen event"""
        from ultracore.database.models import SavingsAccountModel
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.status = 'frozen'
    
    async def _handle_account_dormant(self, event: Dict[str, Any], session):
        """Handle account dormant event"""
        from ultracore.database.models import SavingsAccountModel
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.status = 'dormant'
            account.dormant_since = datetime.fromisoformat(event['event_timestamp'])
    
    async def _handle_tfn_provided(self, event: Dict[str, Any], session):
        """Handle TFN provided event"""
        from ultracore.database.models import SavingsAccountModel
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            data = event['event_data']
            account.tfn = data['tfn']
            account.withholding_tax_rate = Decimal('0.00')
    
    # ========================================================================
    # Transaction Handlers
    # ========================================================================
    
    async def _handle_deposit(self, event: Dict[str, Any], session):
        """Handle deposit event"""
        from ultracore.database.models import SavingsAccountModel, SavingsTransactionModel
        
        data = event['event_data']
        
        # Update account balance
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.balance = Decimal(str(data['balance_after']))
            account.available_balance = Decimal(str(data['balance_after']))
            account.last_transaction_date = datetime.fromisoformat(event['event_timestamp'])
        
        # Create transaction record
        transaction = SavingsTransactionModel(
            transaction_id=data['transaction_id'],
            account_id=event['aggregate_id'],
            tenant_id=event['tenant_id'],
            transaction_type='deposit',
            amount=Decimal(str(data['amount'])),
            balance_before=Decimal(str(data['balance_before'])),
            balance_after=Decimal(str(data['balance_after'])),
            reference_number=data.get('reference_number'),
            description=data.get('description'),
            transaction_date=datetime.fromisoformat(event['event_timestamp']),
            created_by=event['user_id'],
        )
        
        session.add(transaction)
    
    async def _handle_withdrawal(self, event: Dict[str, Any], session):
        """Handle withdrawal event"""
        from ultracore.database.models import SavingsAccountModel, SavingsTransactionModel
        
        data = event['event_data']
        
        # Update account balance
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.balance = Decimal(str(data['balance_after']))
            account.available_balance = Decimal(str(data['balance_after']))
            account.last_transaction_date = datetime.fromisoformat(event['event_timestamp'])
        
        # Create transaction record
        transaction = SavingsTransactionModel(
            transaction_id=data['transaction_id'],
            account_id=event['aggregate_id'],
            tenant_id=event['tenant_id'],
            transaction_type='withdrawal',
            amount=Decimal(str(data['amount'])),  # Will be negative
            balance_before=Decimal(str(data['balance_before'])),
            balance_after=Decimal(str(data['balance_after'])),
            reference_number=data.get('reference_number'),
            description=data.get('description'),
            transaction_date=datetime.fromisoformat(event['event_timestamp']),
            created_by=event['user_id'],
        )
        
        session.add(transaction)
    
    async def _handle_transfer_in(self, event: Dict[str, Any], session):
        """Handle transfer in event"""
        # Similar to deposit
        await self._handle_deposit(event, session)
    
    async def _handle_transfer_out(self, event: Dict[str, Any], session):
        """Handle transfer out event"""
        # Similar to withdrawal
        await self._handle_withdrawal(event, session)
    
    # ========================================================================
    # Interest Handlers
    # ========================================================================
    
    async def _handle_interest_accrued(self, event: Dict[str, Any], session):
        """Handle interest accrued event"""
        from ultracore.database.models import SavingsAccountModel
        
        data = event['event_data']
        
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.accrued_interest = Decimal(str(data['total_accrued']))
    
    async def _handle_interest_posted(self, event: Dict[str, Any], session):
        """Handle interest posted event"""
        from ultracore.database.models import SavingsAccountModel, SavingsTransactionModel
        
        data = event['event_data']
        
        # Update account
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.balance = Decimal(str(data['balance_after']))
            account.available_balance = Decimal(str(data['balance_after']))
            account.accrued_interest = Decimal('0.00')
            account.last_interest_posting_date = datetime.fromisoformat(event['event_timestamp'])
        
        # Create transaction
        transaction = SavingsTransactionModel(
            transaction_id=data['transaction_id'],
            account_id=event['aggregate_id'],
            tenant_id=event['tenant_id'],
            transaction_type='interest_posting',
            amount=Decimal(str(data['net_interest'])),
            balance_before=Decimal(str(data['balance_before'])),
            balance_after=Decimal(str(data['balance_after'])),
            description=f"Interest posted: ${data['gross_interest']} (tax: ${data['tax_withheld']})",
            transaction_date=datetime.fromisoformat(event['event_timestamp']),
            created_by='system',
        )
        
        session.add(transaction)
    
    async def _handle_bonus_earned(self, event: Dict[str, Any], session):
        """Handle bonus interest earned event"""
        logger.info(f"Bonus interest earned: {event['event_data']}")
    
    async def _handle_bonus_forfeited(self, event: Dict[str, Any], session):
        """Handle bonus interest forfeited event"""
        logger.info(f"Bonus interest forfeited: {event['event_data']}")
    
    async def _handle_withholding_tax(self, event: Dict[str, Any], session):
        """Handle withholding tax deducted event"""
        logger.info(f"Withholding tax deducted: {event['event_data']}")
    
    # ========================================================================
    # Fee Handlers
    # ========================================================================
    
    async def _handle_monthly_fee(self, event: Dict[str, Any], session):
        """Handle monthly fee charged event"""
        from ultracore.database.models import SavingsAccountModel, SavingsTransactionModel
        
        data = event['event_data']
        
        # Update account balance
        account = await session.get(SavingsAccountModel, event['aggregate_id'])
        if account:
            account.balance = Decimal(str(data['balance_after']))
            account.available_balance = Decimal(str(data['balance_after']))
        
        # Create transaction
        transaction = SavingsTransactionModel(
            transaction_id=data['transaction_id'],
            account_id=event['aggregate_id'],
            tenant_id=event['tenant_id'],
            transaction_type='fee',
            amount=Decimal(str(data['fee_amount'])) * -1,  # Negative
            balance_before=Decimal(str(data['balance_before'])),
            balance_after=Decimal(str(data['balance_after'])),
            description=f"Monthly account fee: ${data['fee_amount']}",
            transaction_date=datetime.fromisoformat(event['event_timestamp']),
            created_by='system',
        )
        
        session.add(transaction)
    
    async def _handle_fee_waived(self, event: Dict[str, Any], session):
        """Handle fee waived event"""
        logger.info(f"Fee waived: {event['event_data']}")
    
    async def _handle_withdrawal_fee(self, event: Dict[str, Any], session):
        """Handle withdrawal fee charged event"""
        # Similar to monthly fee
        await self._handle_monthly_fee(event, session)
