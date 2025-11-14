"""
Comprehensive Tests for Savings Module
Tests all components: models, services, events, API, AI/ML, accounting
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from ultracore.domains.savings.models.savings_account import (
    SavingsAccount,
    AccountStatus,
)
from ultracore.domains.savings.models.savings_product import (
    SavingsProduct,
    InterestCalculationMethod,
    InterestPostingFrequency,
    BonusCondition,
)
from ultracore.domains.savings.models.term_deposit import TermDeposit
from ultracore.domains.savings.services.account_service import AccountService
from ultracore.domains.savings.services.interest_calculator import InterestCalculator
from ultracore.domains.savings.services.accounting_integration import SavingsAccountingIntegration
from ultracore.agentic_ai.agents.savings.anya_savings_agent import AnyaSavingsAgent
from ultracore.ml.savings.savings_behavior_predictor import SavingsBehaviorPredictor
from ultracore.ml.savings.dormancy_predictor import DormancyPredictor


class TestSavingsProduct:
    """Test savings product model"""
    
    def test_create_savings_product(self):
        """Test creating a savings product"""
        product = SavingsProduct(
            tenant_id=uuid4(),
            product_code="HIS-001",
            product_name="High Interest Savings",
            product_type="high_interest_savings",
            description="High interest savings account",
            base_interest_rate=Decimal("2.50"),
            bonus_interest_rate=Decimal("2.00"),
            interest_calculation_method=InterestCalculationMethod.DAILY_BALANCE,
            interest_posting_frequency=InterestPostingFrequency.MONTHLY,
            minimum_opening_balance=Decimal("0.00"),
            minimum_balance=Decimal("0.00"),
            monthly_fee=Decimal("0.00"),
            pds_url="https://example.com/pds.pdf",
            kfs_url="https://example.com/kfs.pdf",
        )
        
        assert product.product_code == "HIS-001"
        assert product.base_interest_rate == Decimal("2.50")
        assert product.calculate_total_interest_rate(bonus_earned=True) == Decimal("4.50")
    
    def test_bonus_eligibility(self):
        """Test bonus interest eligibility checking"""
        product = SavingsProduct(
            tenant_id=uuid4(),
            product_code="HIS-001",
            product_name="High Interest Savings",
            product_type="high_interest_savings",
            description="High interest savings account",
            base_interest_rate=Decimal("2.50"),
            bonus_interest_rate=Decimal("2.00"),
            interest_calculation_method=InterestCalculationMethod.DAILY_BALANCE,
            interest_posting_frequency=InterestPostingFrequency.MONTHLY,
            minimum_opening_balance=Decimal("0.00"),
            pds_url="https://example.com/pds.pdf",
            kfs_url="https://example.com/kfs.pdf",
        )
        
        # Add bonus conditions
        product.bonus_conditions = [
            BonusCondition(
                condition_type="minimum_monthly_deposit",
                threshold_amount=Decimal("1000.00"),
                description="Deposit at least $1000 per month",
            ),
            BonusCondition(
                condition_type="no_withdrawals",
                description="Make no withdrawals during the month",
            ),
        ]
        
        # Test eligible
        eligible, _ = product.check_bonus_eligibility(
            monthly_deposits=Decimal("1500.00"),
            withdrawal_count=0,
            balance=Decimal("5000.00"),
        )
        assert eligible is True
        
        # Test not eligible (insufficient deposits)
        eligible, _ = product.check_bonus_eligibility(
            monthly_deposits=Decimal("500.00"),
            withdrawal_count=0,
            balance=Decimal("5000.00"),
        )
        assert eligible is False


class TestSavingsAccount:
    """Test savings account model"""
    
    def test_create_savings_account(self):
        """Test creating a savings account"""
        account = SavingsAccount(
            client_id=uuid4(),
            product_id=uuid4(),
            tenant_id=uuid4(),
            account_number="SA1234567890",
            bsb="062000",
            account_name="Test Savings",
            account_type="savings",
            status=AccountStatus.ACTIVE,
        )
        
        assert account.account_number == "SA1234567890"
        assert account.status == AccountStatus.ACTIVE
        assert account.balance == Decimal("0.00")
    
    def test_tfn_withholding_tax(self):
        """Test TFN withholding tax calculation"""
        # Without TFN
        account = SavingsAccount(
            client_id=uuid4(),
            product_id=uuid4(),
            tenant_id=uuid4(),
            account_number="SA1234567890",
            bsb="062000",
            account_name="Test Savings",
            account_type="savings",
        )
        assert account.withholding_tax_rate == Decimal("47.00")
        
        # With TFN
        account.tfn = "123456789"
        account.update_withholding_tax_rate()
        assert account.withholding_tax_rate == Decimal("0.00")
    
    def test_can_deposit(self):
        """Test deposit validation"""
        account = SavingsAccount(
            client_id=uuid4(),
            product_id=uuid4(),
            tenant_id=uuid4(),
            account_number="SA1234567890",
            bsb="062000",
            account_name="Test Savings",
            account_type="savings",
            status=AccountStatus.ACTIVE,
        )
        
        can_deposit, reason = account.can_deposit(Decimal("100.00"))
        assert can_deposit is True
        
        # Test frozen account
        account.status = AccountStatus.FROZEN
        can_deposit, reason = account.can_deposit(Decimal("100.00"))
        assert can_deposit is False


class TestInterestCalculator:
    """Test interest calculation service"""
    
    def test_daily_interest_calculation(self):
        """Test daily interest calculation"""
        gross, tax, net = InterestCalculator.calculate_daily_interest(
            balance=Decimal("10000.00"),
            annual_rate=Decimal("3.65"),
            withholding_tax_rate=Decimal("0.00"),
        )
        
        # Expected: 10000 * 0.0365 / 365 = 1.00
        assert gross == Decimal("1.00")
        assert tax == Decimal("0.00")
        assert net == Decimal("1.00")
    
    def test_daily_interest_with_withholding_tax(self):
        """Test daily interest with withholding tax"""
        gross, tax, net = InterestCalculator.calculate_daily_interest(
            balance=Decimal("10000.00"),
            annual_rate=Decimal("3.65"),
            withholding_tax_rate=Decimal("47.00"),
        )
        
        assert gross == Decimal("1.00")
        assert tax == Decimal("0.47")
        assert net == Decimal("0.53")
    
    def test_period_interest_daily_balance_method(self):
        """Test period interest calculation using daily balance method"""
        daily_balances = [
            (date(2025, 1, 1), Decimal("10000.00")),
            (date(2025, 1, 2), Decimal("10000.00")),
            (date(2025, 1, 3), Decimal("10000.00")),
        ]
        
        gross, tax, net = InterestCalculator.calculate_period_interest(
            daily_balances=daily_balances,
            annual_rate=Decimal("3.65"),
            calculation_method=InterestCalculationMethod.DAILY_BALANCE,
            withholding_tax_rate=Decimal("0.00"),
        )
        
        # Expected: 3 days * 1.00 = 3.00
        assert gross == Decimal("3.00")
    
    def test_interest_projection(self):
        """Test interest projection"""
        gross, tax, net = InterestCalculator.project_interest(
            principal=Decimal("10000.00"),
            annual_rate=Decimal("4.00"),
            months=12,
            posting_frequency=InterestPostingFrequency.MONTHLY,
            withholding_tax_rate=Decimal("0.00"),
        )
        
        # Should be approximately $400 with monthly compounding
        assert gross > Decimal("400.00")
        assert gross < Decimal("410.00")  # With compounding


class TestAccountService:
    """Test account lifecycle service"""
    
    def test_create_account(self):
        """Test account creation"""
        product = SavingsProduct(
            product_id=uuid4(),
            tenant_id=uuid4(),
            product_code="HIS-001",
            product_name="High Interest Savings",
            product_type="high_interest_savings",
            description="Test product",
            base_interest_rate=Decimal("2.50"),
            interest_calculation_method=InterestCalculationMethod.DAILY_BALANCE,
            interest_posting_frequency=InterestPostingFrequency.MONTHLY,
            minimum_opening_balance=Decimal("0.00"),
            pds_url="https://example.com/pds.pdf",
            kfs_url="https://example.com/kfs.pdf",
        )
        
        account = AccountService.create_account(
            client_id=uuid4(),
            product=product,
            account_name="Test Account",
            bsb="062000",
            account_number="SA1234567890",
            tenant_id=uuid4(),
            initial_deposit=Decimal("100.00"),
            tfn="123456789",
        )
        
        assert account.balance == Decimal("100.00")
        assert account.tfn == "123456789"
        assert account.withholding_tax_rate == Decimal("0.00")
    
    def test_make_deposit(self):
        """Test making a deposit"""
        account = SavingsAccount(
            client_id=uuid4(),
            product_id=uuid4(),
            tenant_id=uuid4(),
            account_number="SA1234567890",
            bsb="062000",
            account_name="Test Savings",
            account_type="savings",
            status=AccountStatus.ACTIVE,
            balance=Decimal("1000.00"),
            available_balance=Decimal("1000.00"),
        )
        
        updated_account, transaction = AccountService.make_deposit(
            account=account,
            amount=Decimal("500.00"),
            source="External",
            reference="DEP001",
            description="Test deposit",
            tenant_id=uuid4(),
        )
        
        assert updated_account.balance == Decimal("1500.00")
        assert transaction.amount == Decimal("500.00")
        assert transaction.balance_after == Decimal("1500.00")
    
    def test_make_withdrawal(self):
        """Test making a withdrawal"""
        account = SavingsAccount(
            client_id=uuid4(),
            product_id=uuid4(),
            tenant_id=uuid4(),
            account_number="SA1234567890",
            bsb="062000",
            account_name="Test Savings",
            account_type="savings",
            status=AccountStatus.ACTIVE,
            balance=Decimal("1000.00"),
            available_balance=Decimal("1000.00"),
        )
        
        updated_account, transaction = AccountService.make_withdrawal(
            account=account,
            amount=Decimal("300.00"),
            destination="External",
            reference="WD001",
            description="Test withdrawal",
            tenant_id=uuid4(),
        )
        
        assert updated_account.balance == Decimal("700.00")
        assert transaction.amount == Decimal("-300.00")


class TestAccountingIntegration:
    """Test accounting integration"""
    
    def test_deposit_journal_entries(self):
        """Test journal entries for deposit"""
        from ultracore.domains.savings.models.transaction import SavingsTransaction, TransactionType
        
        transaction = SavingsTransaction(
            account_id=uuid4(),
            tenant_id=uuid4(),
            transaction_type=TransactionType.DEPOSIT,
            amount=Decimal("1000.00"),
            balance_before=Decimal("5000.00"),
            balance_after=Decimal("6000.00"),
            reference_number="DEP001",
            description="Test deposit",
        )
        
        entries = SavingsAccountingIntegration.generate_journal_entries(
            transaction=transaction,
            tenant_id=uuid4(),
        )
        
        assert len(entries) == 2
        assert entries[0]['debit'] == 1000.00  # Cash at Bank DR
        assert entries[1]['credit'] == 1000.00  # Savings Deposits CR
        assert SavingsAccountingIntegration.verify_journal_balance(entries) is True
    
    def test_interest_posting_journal_entries(self):
        """Test journal entries for interest posting"""
        from ultracore.domains.savings.models.transaction import SavingsTransaction, TransactionType
        
        transaction = SavingsTransaction(
            account_id=uuid4(),
            tenant_id=uuid4(),
            transaction_type=TransactionType.INTEREST_POSTING,
            amount=Decimal("50.00"),
            balance_before=Decimal("10000.00"),
            balance_after=Decimal("10050.00"),
            reference_number="INT001",
            description="Interest posting",
        )
        
        entries = SavingsAccountingIntegration.generate_journal_entries(
            transaction=transaction,
            tenant_id=uuid4(),
        )
        
        assert len(entries) == 2
        assert SavingsAccountingIntegration.verify_journal_balance(entries) is True


class TestAnyaSavingsAgent:
    """Test Anya AI agent"""
    
    def test_recommend_savings_product(self):
        """Test product recommendation"""
        agent = AnyaSavingsAgent()
        
        products = [
            SavingsProduct(
                product_id=uuid4(),
                tenant_id=uuid4(),
                product_code="HIS-001",
                product_name="High Interest Savings",
                product_type="high_interest_savings",
                description="High interest savings",
                base_interest_rate=Decimal("2.50"),
                bonus_interest_rate=Decimal("2.00"),
                interest_calculation_method=InterestCalculationMethod.DAILY_BALANCE,
                interest_posting_frequency=InterestPostingFrequency.MONTHLY,
                minimum_opening_balance=Decimal("0.00"),
                monthly_fee=Decimal("0.00"),
                pds_url="https://example.com/pds.pdf",
                kfs_url="https://example.com/kfs.pdf",
            ),
        ]
        
        recommendation = agent.recommend_savings_product(
            customer_age=30,
            monthly_income=Decimal("5000.00"),
            current_savings=Decimal("10000.00"),
            available_products=products,
        )
        
        assert recommendation['recommended_product'] is not None
        assert 'projected_returns' in recommendation
    
    def test_create_savings_plan(self):
        """Test savings plan creation"""
        agent = AnyaSavingsAgent()
        
        plan = agent.create_savings_plan(
            current_balance=Decimal("5000.00"),
            target_amount=Decimal("20000.00"),
            target_date=date.today() + timedelta(days=365),
            annual_interest_rate=Decimal("4.00"),
            current_monthly_deposit=Decimal("1000.00"),
        )
        
        assert 'goal' in plan
        assert 'required_action' in plan
        assert plan['goal']['target_amount'] == 20000.00


class TestSavingsBehaviorPredictor:
    """Test ML savings behavior predictor"""
    
    def test_predict_savings_propensity(self):
        """Test savings propensity prediction"""
        predictor = SavingsBehaviorPredictor()
        
        prediction = predictor.predict_savings_propensity(
            age=30,
            monthly_income=Decimal("5000.00"),
            employment_status="employed",
            current_balance=Decimal("10000.00"),
            transaction_history=[
                {'transaction_type': 'deposit', 'amount': 1000, 'balance_after': 10000},
                {'transaction_type': 'deposit', 'amount': 1000, 'balance_after': 11000},
            ],
            account_age_months=12,
            has_tfn=True,
            product_type="high_interest_savings",
        )
        
        assert 'propensity_score' in prediction
        assert 0 <= prediction['propensity_score'] <= 100
        assert 'recommended_monthly_deposit' in prediction


class TestDormancyPredictor:
    """Test ML dormancy predictor"""
    
    def test_predict_dormancy_risk(self):
        """Test dormancy risk prediction"""
        predictor = DormancyPredictor()
        
        prediction = predictor.predict_dormancy_risk(
            account_id="SA1234567890",
            last_transaction_date=datetime.utcnow() - timedelta(days=200),
            account_opened_date=datetime.utcnow() - timedelta(days=400),
            transaction_history=[
                {'transaction_type': 'deposit', 'amount': 1000, 'transaction_date': datetime.utcnow() - timedelta(days=200)},
            ],
            current_balance=Decimal("5000.00"),
            customer_age=30,
            has_tfn=True,
            product_type="savings",
        )
        
        assert 'risk_score' in prediction
        assert 'risk_category' in prediction
        assert 'days_until_dormancy' in prediction
