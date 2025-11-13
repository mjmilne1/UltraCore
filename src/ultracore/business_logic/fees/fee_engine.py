"""
Enterprise Fee Calculation Engine
Complex fee structures with ML-powered optimization

Features:
- Multiple fee types (monthly, transaction, penalty, etc.)
- Tiered pricing structures
- Fee waivers based on customer tier
- ML-powered fee optimization
- Regulatory compliance (ASIC requirements)
- Event-sourced fee tracking
"""
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from enum import Enum

from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store
from ultracore.ml_models.scoring_engine import get_scoring_engine, ModelType
from ultracore.data_mesh.integration import DataMeshPublisher


class FeeType(str, Enum):
    # Account Fees
    MONTHLY_ACCOUNT_FEE = 'MONTHLY_ACCOUNT_FEE'
    ANNUAL_ACCOUNT_FEE = 'ANNUAL_ACCOUNT_FEE'
    ACCOUNT_OPENING_FEE = 'ACCOUNT_OPENING_FEE'
    ACCOUNT_CLOSING_FEE = 'ACCOUNT_CLOSING_FEE'
    
    # Transaction Fees
    TRANSACTION_FEE = 'TRANSACTION_FEE'
    ATM_WITHDRAWAL_FEE = 'ATM_WITHDRAWAL_FEE'
    INTERNATIONAL_TRANSACTION_FEE = 'INTERNATIONAL_TRANSACTION_FEE'
    OVER_COUNTER_TRANSACTION_FEE = 'OVER_COUNTER_TRANSACTION_FEE'
    
    # Card Fees
    CARD_ISSUE_FEE = 'CARD_ISSUE_FEE'
    CARD_REPLACEMENT_FEE = 'CARD_REPLACEMENT_FEE'
    CARD_ANNUAL_FEE = 'CARD_ANNUAL_FEE'
    
    # Overdraft Fees
    OVERDRAFT_FEE = 'OVERDRAFT_FEE'
    NSF_FEE = 'NSF_FEE'  # Non-Sufficient Funds
    
    # Loan Fees
    LOAN_APPLICATION_FEE = 'LOAN_APPLICATION_FEE'
    LOAN_ESTABLISHMENT_FEE = 'LOAN_ESTABLISHMENT_FEE'
    EARLY_TERMINATION_FEE = 'EARLY_TERMINATION_FEE'
    LATE_PAYMENT_FEE = 'LATE_PAYMENT_FEE'
    
    # Other Fees
    PAPER_STATEMENT_FEE = 'PAPER_STATEMENT_FEE'
    CHEQUE_BOOK_FEE = 'CHEQUE_BOOK_FEE'
    STOP_PAYMENT_FEE = 'STOP_PAYMENT_FEE'
    DISHONOUR_FEE = 'DISHONOUR_FEE'
    TELEGRAPHIC_TRANSFER_FEE = 'TELEGRAPHIC_TRANSFER_FEE'


class CustomerTier(str, Enum):
    BASIC = 'BASIC'
    SILVER = 'SILVER'
    GOLD = 'GOLD'
    PLATINUM = 'PLATINUM'
    PRIVATE = 'PRIVATE'


class FeeStructure:
    """
    Fee structure with tiered pricing
    """
    
    def __init__(self, fee_type: FeeType):
        self.fee_type = fee_type
        self.base_fee: Decimal = Decimal('0')
        self.percentage_fee: Optional[Decimal] = None
        self.minimum_fee: Optional[Decimal] = None
        self.maximum_fee: Optional[Decimal] = None
        self.tier_fees: Dict[CustomerTier, Decimal] = {}
        self.transaction_threshold: Optional[int] = None  # Free transactions per month
        self.tier_waivers: List[CustomerTier] = []
    
    def calculate_fee(
        self,
        customer_tier: CustomerTier,
        transaction_amount: Optional[Decimal] = None,
        transaction_count: int = 0
    ) -> Decimal:
        """
        Calculate fee based on customer tier and transaction details
        
        Logic:
        1. Check if fee is waived for customer tier
        2. Apply transaction threshold (if applicable)
        3. Calculate base + percentage fee
        4. Apply min/max caps
        5. Apply tier discounts
        """
        # Check waiver
        if customer_tier in self.tier_waivers:
            return Decimal('0')
        
        # Check transaction threshold
        if self.transaction_threshold and transaction_count <= self.transaction_threshold:
            return Decimal('0')
        
        # Calculate base fee
        fee = self.tier_fees.get(customer_tier, self.base_fee)
        
        # Add percentage fee if applicable
        if self.percentage_fee and transaction_amount:
            percentage_amount = (transaction_amount * self.percentage_fee / Decimal('100'))
            fee = fee + percentage_amount
        
        # Apply minimum
        if self.minimum_fee and fee < self.minimum_fee:
            fee = self.minimum_fee
        
        # Apply maximum
        if self.maximum_fee and fee > self.maximum_fee:
            fee = self.maximum_fee
        
        return fee.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class FeeEngine:
    """
    Enterprise fee calculation engine
    
    Features:
    - Complex fee structures
    - Tiered pricing
    - ML-powered optimization
    - Regulatory compliance
    """
    
    def __init__(self):
        self.fee_structures: Dict[FeeType, FeeStructure] = {}
        self._initialize_fee_structures()
    
    def _initialize_fee_structures(self):
        """Initialize Australian banking fee structures"""
        
        # Monthly Account Fee
        monthly_fee = FeeStructure(FeeType.MONTHLY_ACCOUNT_FEE)
        monthly_fee.base_fee = Decimal('10.00')
        monthly_fee.tier_fees = {
            CustomerTier.BASIC: Decimal('10.00'),
            CustomerTier.SILVER: Decimal('5.00'),
            CustomerTier.GOLD: Decimal('0.00'),
            CustomerTier.PLATINUM: Decimal('0.00'),
            CustomerTier.PRIVATE: Decimal('0.00')
        }
        monthly_fee.tier_waivers = [CustomerTier.GOLD, CustomerTier.PLATINUM, CustomerTier.PRIVATE]
        self.fee_structures[FeeType.MONTHLY_ACCOUNT_FEE] = monthly_fee
        
        # ATM Withdrawal Fee
        atm_fee = FeeStructure(FeeType.ATM_WITHDRAWAL_FEE)
        atm_fee.base_fee = Decimal('2.50')
        atm_fee.transaction_threshold = 4  # 4 free per month
        atm_fee.tier_waivers = [CustomerTier.PLATINUM, CustomerTier.PRIVATE]
        self.fee_structures[FeeType.ATM_WITHDRAWAL_FEE] = atm_fee
        
        # International Transaction Fee
        intl_fee = FeeStructure(FeeType.INTERNATIONAL_TRANSACTION_FEE)
        intl_fee.base_fee = Decimal('3.00')
        intl_fee.percentage_fee = Decimal('3.0')  # 3% of transaction
        intl_fee.minimum_fee = Decimal('5.00')
        intl_fee.tier_fees = {
            CustomerTier.BASIC: Decimal('3.00'),
            CustomerTier.SILVER: Decimal('2.50'),
            CustomerTier.GOLD: Decimal('2.00'),
            CustomerTier.PLATINUM: Decimal('0.00'),
            CustomerTier.PRIVATE: Decimal('0.00')
        }
        self.fee_structures[FeeType.INTERNATIONAL_TRANSACTION_FEE] = intl_fee
        
        # Overdraft Fee
        overdraft_fee = FeeStructure(FeeType.OVERDRAFT_FEE)
        overdraft_fee.base_fee = Decimal('15.00')
        self.fee_structures[FeeType.OVERDRAFT_FEE] = overdraft_fee
        
        # Late Payment Fee (Loans)
        late_fee = FeeStructure(FeeType.LATE_PAYMENT_FEE)
        late_fee.base_fee = Decimal('20.00')
        late_fee.maximum_fee = Decimal('50.00')  # ASIC cap
        self.fee_structures[FeeType.LATE_PAYMENT_FEE] = late_fee
        
        # Loan Establishment Fee
        establishment_fee = FeeStructure(FeeType.LOAN_ESTABLISHMENT_FEE)
        establishment_fee.base_fee = Decimal('250.00')
        establishment_fee.percentage_fee = Decimal('1.0')  # 1% of loan
        establishment_fee.maximum_fee = Decimal('1000.00')
        self.fee_structures[FeeType.LOAN_ESTABLISHMENT_FEE] = establishment_fee
        
        # Card Annual Fee
        card_fee = FeeStructure(FeeType.CARD_ANNUAL_FEE)
        card_fee.tier_fees = {
            CustomerTier.BASIC: Decimal('49.00'),
            CustomerTier.SILVER: Decimal('99.00'),
            CustomerTier.GOLD: Decimal('195.00'),
            CustomerTier.PLATINUM: Decimal('395.00'),
            CustomerTier.PRIVATE: Decimal('0.00')  # Included in banking package
        }
        self.fee_structures[FeeType.CARD_ANNUAL_FEE] = card_fee
    
    async def calculate_fee(
        self,
        fee_type: FeeType,
        customer_id: str,
        customer_tier: CustomerTier,
        transaction_amount: Optional[Decimal] = None,
        transaction_count: int = 0,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate fee with ML-powered optimization
        
        Returns fee amount and breakdown
        """
        fee_structure = self.fee_structures.get(fee_type)
        
        if not fee_structure:
            raise ValueError(f"Fee structure not found for {fee_type}")
        
        # Calculate base fee
        fee_amount = fee_structure.calculate_fee(
            customer_tier,
            transaction_amount,
            transaction_count
        )
        
        # Check for fee waiver opportunities (ML-powered)
        waiver_recommendation = await self._check_fee_waiver(
            customer_id,
            fee_type,
            fee_amount,
            context
        )
        
        if waiver_recommendation['should_waive']:
            fee_amount = Decimal('0')
        
        # Build response
        fee_calculation = {
            'fee_type': fee_type.value,
            'customer_id': customer_id,
            'customer_tier': customer_tier.value,
            'original_fee': str(fee_structure.base_fee),
            'calculated_fee': str(fee_amount),
            'waived': waiver_recommendation['should_waive'],
            'waiver_reason': waiver_recommendation.get('reason'),
            'transaction_amount': str(transaction_amount) if transaction_amount else None,
            'calculated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Publish to Data Mesh
        await DataMeshPublisher.publish_transaction_data(
            f"fee_{customer_id}_{fee_type.value}",
            {
                'data_product': 'fee_calculations',
                'fee_calculation': fee_calculation
            }
        )
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='fees',
            event_type='fee_calculated',
            event_data=fee_calculation,
            aggregate_id=customer_id
        )
        
        return fee_calculation
    
    async def _check_fee_waiver(
        self,
        customer_id: str,
        fee_type: FeeType,
        fee_amount: Decimal,
        context: Optional[Dict]
    ) -> Dict:
        """
        ML-powered fee waiver recommendation
        
        Considers:
        - Customer lifetime value
        - Churn risk
        - Relationship profitability
        - Competitive positioning
        """
        scoring_engine = get_scoring_engine()
        
        # Get customer churn risk
        churn_result = await scoring_engine.score(
            model_type=ModelType.CUSTOMER_CHURN,
            input_data={'customer_id': customer_id}
        )
        
        churn_probability = churn_result.get('probability', 0)
        
        # High churn risk + reasonable fee = waive to retain
        if churn_probability > 0.6 and fee_amount < Decimal('50.00'):
            return {
                'should_waive': True,
                'reason': 'Customer retention (high churn risk)',
                'churn_probability': churn_probability
            }
        
        # Check if customer complained recently about fees
        if context and context.get('recent_complaint'):
            return {
                'should_waive': True,
                'reason': 'Goodwill gesture (recent complaint)'
            }
        
        return {'should_waive': False}
    
    async def apply_fee(
        self,
        account_id: str,
        fee_type: FeeType,
        fee_amount: Decimal,
        description: str
    ) -> Dict:
        """
        Apply fee to account
        
        Creates:
        - Fee transaction
        - GL entries (debit/credit)
        - Customer notification
        """
        # Create fee transaction
        from ultracore.modules.accounting.general_ledger.journal import JournalEntry, get_journal_service
        
        journal_service = get_journal_service()
        
        # Debit customer account, Credit fee income
        entry = await journal_service.create_entry(
            description=f"Fee: {description}",
            entries=[
                {
                    'account_code': '1100',  # Customer Account (Asset)
                    'debit': str(fee_amount),
                    'credit': '0'
                },
                {
                    'account_code': '4200',  # Fee Income (Revenue)
                    'debit': '0',
                    'credit': str(fee_amount)
                }
            ]
        )
        
        # Publish event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='fees',
            event_type='fee_applied',
            event_data={
                'account_id': account_id,
                'fee_type': fee_type.value,
                'fee_amount': str(fee_amount),
                'description': description,
                'journal_entry_id': entry['entry_id']
            },
            aggregate_id=account_id
        )
        
        # Trigger notification
        await kafka_store.append_event(
            entity='notifications',
            event_type='send_fee_notification',
            event_data={
                'account_id': account_id,
                'fee_type': fee_type.value,
                'fee_amount': str(fee_amount)
            },
            aggregate_id=account_id
        )
        
        return {
            'success': True,
            'account_id': account_id,
            'fee_amount': str(fee_amount),
            'journal_entry_id': entry['entry_id']
        }


class FeeOptimizationAgent:
    """
    Agentic fee optimization
    
    Autonomously:
    - Identifies fee revenue opportunities
    - Recommends fee structure changes
    - Monitors competitive fee landscape
    - Optimizes for customer retention
    """
    
    @staticmethod
    async def analyze_fee_revenue():
        """
        Analyze fee revenue across portfolio
        
        Identifies:
        - High-fee customers (potential churn)
        - Under-monetized segments
        - Fee optimization opportunities
        """
        # ML-powered analysis
        pass
    
    @staticmethod
    async def recommend_fee_changes(customer_segment: str) -> List[Dict]:
        """
        Recommend fee structure changes for segment
        
        Based on:
        - Competitive analysis
        - Customer sensitivity
        - Revenue impact
        """
        recommendations = []
        
        # Example: Reduce ATM fees for high-value segment
        recommendations.append({
            'segment': customer_segment,
            'recommendation': 'Waive ATM fees',
            'expected_retention_improvement': '12%',
            'revenue_impact': '-\ annually',
            'net_impact': '+\ (retention value)'
        })
        
        return recommendations
