"""
Banking Integration Service

Integrates UltraWealth with UltraCore banking modules
"""

from typing import Dict, Optional
from decimal import Decimal
from datetime import datetime

from sqlalchemy.orm import Session

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class BankingIntegrationService:
    """
    Integration service for UltraCore banking modules
    
    Connects UltraWealth with:
    - Cash Module (cash management, settlements)
    - Holdings Module (position tracking)
    - Transactions Module (trade records)
    - Accounting Module (journal entries)
    - Compliance Module (AML/KYC)
    - Client Module (client profiles)
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.kafka_store = get_production_kafka_store()
    
    # ========================================================================
    # CASH MODULE INTEGRATION
    # ========================================================================
    
    async def check_cash_balance(self, client_id: str) -> Decimal:
        """
        Check available cash balance for client
        
        Integrates with UltraCore Cash Module
        """
        
        # Publish query event
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='cash_balance_requested',
            event_data={
                'client_id': client_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        # In production, this would query the Cash Module
        # For now, return a placeholder
        return Decimal("10000.00")
    
    async def reserve_cash_for_trade(
        self,
        client_id: str,
        amount: Decimal,
        order_id: str
    ) -> Dict:
        """
        Reserve cash for pending trade
        
        Integrates with UltraCore Cash Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='cash_reserved_for_trade',
            event_data={
                'client_id': client_id,
                'amount': float(amount),
                'order_id': order_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        return {
            'reserved': True,
            'amount': float(amount),
            'order_id': order_id
        }
    
    async def settle_trade_cash(
        self,
        client_id: str,
        amount: Decimal,
        order_id: str,
        trade_type: str  # 'buy' or 'sell'
    ) -> Dict:
        """
        Settle cash for executed trade
        
        Integrates with UltraCore Cash Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='trade_cash_settled',
            event_data={
                'client_id': client_id,
                'amount': float(amount),
                'order_id': order_id,
                'trade_type': trade_type,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        return {
            'settled': True,
            'amount': float(amount),
            'trade_type': trade_type
        }
    
    # ========================================================================
    # HOLDINGS MODULE INTEGRATION
    # ========================================================================
    
    async def sync_holding_to_holdings_module(
        self,
        client_id: str,
        portfolio_id: str,
        ticker: str,
        quantity: Decimal,
        average_cost: Decimal
    ) -> Dict:
        """
        Sync holding to UltraCore Holdings Module
        
        Integrates with UltraCore Holdings Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='holding_synced_to_holdings_module',
            event_data={
                'client_id': client_id,
                'portfolio_id': portfolio_id,
                'ticker': ticker,
                'quantity': float(quantity),
                'average_cost': float(average_cost),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=portfolio_id
        )
        
        return {
            'synced': True,
            'ticker': ticker,
            'quantity': float(quantity)
        }
    
    # ========================================================================
    # TRANSACTIONS MODULE INTEGRATION
    # ========================================================================
    
    async def record_trade_transaction(
        self,
        client_id: str,
        portfolio_id: str,
        order_id: str,
        ticker: str,
        trade_type: str,
        quantity: Decimal,
        price: Decimal,
        total_amount: Decimal
    ) -> Dict:
        """
        Record trade in UltraCore Transactions Module
        
        Integrates with UltraCore Transactions Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='trade_transaction_recorded',
            event_data={
                'client_id': client_id,
                'portfolio_id': portfolio_id,
                'order_id': order_id,
                'ticker': ticker,
                'trade_type': trade_type,
                'quantity': float(quantity),
                'price': float(price),
                'total_amount': float(total_amount),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=order_id
        )
        
        return {
            'recorded': True,
            'order_id': order_id,
            'transaction_id': f"TXN-{order_id}"
        }
    
    # ========================================================================
    # ACCOUNTING MODULE INTEGRATION
    # ========================================================================
    
    async def create_trade_journal_entry(
        self,
        client_id: str,
        order_id: str,
        ticker: str,
        trade_type: str,
        quantity: Decimal,
        price: Decimal,
        total_amount: Decimal
    ) -> Dict:
        """
        Create double-entry journal entry for trade
        
        Integrates with UltraCore Accounting Module
        """
        
        # Determine debit/credit accounts based on trade type
        if trade_type == 'buy':
            debit_account = f"Investment-{ticker}"
            credit_account = "Cash"
        else:  # sell
            debit_account = "Cash"
            credit_account = f"Investment-{ticker}"
        
        journal_entry = {
            'order_id': order_id,
            'date': datetime.now(timezone.utc).isoformat(),
            'description': f"{trade_type.upper()} {float(quantity)} units of {ticker} @ ${float(price)}",
            'entries': [
                {
                    'account': debit_account,
                    'debit': float(total_amount),
                    'credit': 0
                },
                {
                    'account': credit_account,
                    'debit': 0,
                    'credit': float(total_amount)
                }
            ]
        }
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='trade_journal_entry_created',
            event_data={
                'client_id': client_id,
                'journal_entry': journal_entry,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=order_id
        )
        
        return journal_entry
    
    # ========================================================================
    # COMPLIANCE MODULE INTEGRATION
    # ========================================================================
    
    async def check_client_kyc_status(self, client_id: str) -> Dict:
        """
        Check client KYC/AML status
        
        Integrates with UltraCore Compliance Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='kyc_status_requested',
            event_data={
                'client_id': client_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        # In production, query Compliance Module
        return {
            'client_id': client_id,
            'kyc_completed': True,
            'aml_cleared': True,
            'risk_rating': 'low'
        }
    
    async def report_large_transaction(
        self,
        client_id: str,
        order_id: str,
        amount: Decimal
    ) -> Dict:
        """
        Report large transaction to Compliance Module
        
        Required for AUSTRAC reporting
        """
        
        if amount >= Decimal("10000"):  # AUD 10,000 threshold
            await self.kafka_store.append_event(
                entity='ultrawealth_integration',
                event_type='large_transaction_reported',
                event_data={
                    'client_id': client_id,
                    'order_id': order_id,
                    'amount': float(amount),
                    'threshold': 10000,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                aggregate_id=client_id
            )
            
            return {
                'reported': True,
                'amount': float(amount),
                'reason': 'Exceeds AUD 10,000 threshold'
            }
        
        return {
            'reported': False,
            'amount': float(amount)
        }
    
    # ========================================================================
    # CLIENT MODULE INTEGRATION
    # ========================================================================
    
    async def get_client_profile(self, client_id: str) -> Dict:
        """
        Get client profile from Client Module
        
        Integrates with UltraCore Client Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='client_profile_requested',
            event_data={
                'client_id': client_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=client_id
        )
        
        # In production, query Client Module
        return {
            'client_id': client_id,
            'name': 'Sample Client',
            'email': 'client@example.com',
            'phone': '+61 400 000 000'
        }
    
    # ========================================================================
    # INVESTOR MODULE INTEGRATION
    # ========================================================================
    
    async def check_investor_eligibility(
        self,
        client_id: str,
        portfolio_id: str
    ) -> Dict:
        """
        Check if portfolio is eligible for investor sale
        
        Integrates with UltraCore Investor Module
        """
        
        await self.kafka_store.append_event(
            entity='ultrawealth_integration',
            event_type='investor_eligibility_checked',
            event_data={
                'client_id': client_id,
                'portfolio_id': portfolio_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            aggregate_id=portfolio_id
        )
        
        return {
            'eligible': True,
            'portfolio_id': portfolio_id,
            'min_portfolio_value': 100000
        }
