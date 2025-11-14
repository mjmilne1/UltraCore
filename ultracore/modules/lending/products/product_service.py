"""
Loan Product Service
Manages loan products and interest rate charts
"""

from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
import uuid

from .models import (
    LoanProduct, InterestRateChart, InterestRateChartSlab,
    CreateLoanProductRequest, CreateInterestRateChartRequest,
    LoanProductType, InterestRateType, LoanPurpose, LoanFee
)


class LoanProductService:
    """
    Loan Product Service
    
    Manages:
    - Loan product configuration
    - Interest rate charts
    - Product eligibility
    - Rate calculations
    """
    
    def __init__(self):
        self.products: Dict[str, LoanProduct] = {}
        self.rate_charts: Dict[str, InterestRateChart] = {}
        
    def create_product(
        self,
        request: CreateLoanProductRequest
    ) -> LoanProduct:
        """
        Create a new loan product
        
        Args:
            request: Product creation request
            
        Returns:
            Created product
        """
        product_id = f"PROD-{uuid.uuid4().hex[:12].upper()}"
        
        # Create default interest rate chart
        chart_id = f"CHART-{uuid.uuid4().hex[:12].upper()}"
        
        product = LoanProduct(
            product_id=product_id,
            product_code=request.product_code,
            product_name=request.product_name,
            product_type=request.product_type,
            description=request.description,
            is_active=True,
            available_from=date.today(),
            min_loan_amount=request.min_loan_amount,
            max_loan_amount=request.max_loan_amount,
            min_term_months=request.min_term_months,
            max_term_months=request.max_term_months,
            default_term_months=request.default_term_months,
            interest_rate_chart_id=chart_id,
            rate_type=request.rate_type,
            base_interest_rate=request.base_interest_rate,
            allowed_repayment_frequencies=request.allowed_repayment_frequencies,
            default_repayment_frequency=request.default_repayment_frequency,
            amortization_type=request.amortization_type,
            requires_security=request.requires_security,
            created_by=request.created_by,
            allowed_purposes=[],  # Will be set separately
            fees=[]  # Will be added separately
        )
        
        self.products[product_id] = product
        
        return product
        
    def create_interest_rate_chart(
        self,
        request: CreateInterestRateChartRequest
    ) -> InterestRateChart:
        """
        Create an interest rate chart
        
        Args:
            request: Chart creation request
            
        Returns:
            Created chart
        """
        chart_id = f"CHART-{uuid.uuid4().hex[:12].upper()}"
        
        chart = InterestRateChart(
            chart_id=chart_id,
            chart_name=request.chart_name,
            effective_from=request.effective_from,
            rate_type=request.rate_type,
            slabs=request.slabs,
            is_active=True
        )
        
        self.rate_charts[chart_id] = chart
        
        return chart
        
    def add_fee_to_product(
        self,
        product_id: str,
        fee: LoanFee
    ) -> LoanProduct:
        """Add a fee to a product"""
        product = self.products.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        product.fees.append(fee)
        product.updated_at = datetime.now(timezone.utc)
        
        return product
        
    def get_product(
        self,
        product_id: str
    ) -> Optional[LoanProduct]:
        """Get product by ID"""
        return self.products.get(product_id)
        
    def get_product_by_code(
        self,
        product_code: str
    ) -> Optional[LoanProduct]:
        """Get product by code"""
        for product in self.products.values():
            if product.product_code == product_code.upper():
                return product
        return None
        
    def list_active_products(
        self,
        product_type: Optional[LoanProductType] = None
    ) -> List[LoanProduct]:
        """List all active products"""
        products = [p for p in self.products.values() if p.is_active]
        
        if product_type:
            products = [p for p in products if p.product_type == product_type]
        
        # Filter by availability date
        today = date.today()
        products = [
            p for p in products
            if p.available_from <= today and (p.available_to is None or p.available_to >= today)
        ]
        
        return products
        
    def get_applicable_rate(
        self,
        product_id: str,
        loan_amount: Decimal,
        term_months: int,
        lvr: Optional[Decimal] = None
    ) -> Optional[InterestRateChartSlab]:
        """
        Get applicable interest rate for a loan
        
        Args:
            product_id: Product ID
            loan_amount: Loan amount
            term_months: Loan term
            lvr: Loan-to-Value Ratio
            
        Returns:
            Applicable rate slab or None
        """
        product = self.products.get(product_id)
        if not product:
            return None
        
        chart = self.rate_charts.get(product.interest_rate_chart_id)
        if not chart:
            return None
        
        return chart.get_applicable_rate(loan_amount, term_months, lvr)
        
    def calculate_total_fees(
        self,
        product_id: str,
        loan_amount: Decimal
    ) -> Decimal:
        """
        Calculate total upfront fees for a loan
        
        Args:
            product_id: Product ID
            loan_amount: Loan amount
            
        Returns:
            Total fees
        """
        product = self.products.get(product_id)
        if not product:
            return Decimal("0")
        
        total = Decimal("0")
        
        for fee in product.fees:
            if fee.is_percentage:
                total += loan_amount * (fee.amount / Decimal("100"))
            else:
                total += fee.amount
        
        return total
        
    def deactivate_product(
        self,
        product_id: str
    ) -> LoanProduct:
        """Deactivate a product"""
        product = self.products.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        product.is_active = False
        product.available_to = date.today()
        product.updated_at = datetime.now(timezone.utc)
        
        return product


# ============================================================================
# PREDEFINED PRODUCTS FOR AUSTRALIAN DIGITAL BANK
# ============================================================================

def create_default_products(service: LoanProductService) -> List[LoanProduct]:
    """
    Create default loan products for Australian digital bank
    
    Returns:
        List of created products
    """
    products = []
    
    # 1. Personal Loan - Standard
    pl_standard = service.create_product(CreateLoanProductRequest(
        product_code="PL-STANDARD-001",
        product_name="Personal Loan - Standard",
        product_type=LoanProductType.PERSONAL,
        description="Unsecured personal loan for general purposes",
        min_loan_amount=Decimal("5000"),
        max_loan_amount=Decimal("50000"),
        min_term_months=12,
        max_term_months=84,
        default_term_months=36,
        base_interest_rate=Decimal("0.0850"),  # 8.50%
        rate_type=InterestRateType.FIXED,
        allowed_repayment_frequencies=[
            "monthly", "fortnightly", "weekly"
        ],
        default_repayment_frequency="monthly",
        amortization_type="principal_and_interest",
        requires_security=False,
        created_by="system"
    ))
    
    # Add fees
    service.add_fee_to_product(pl_standard.product_id, LoanFee(
        fee_id="FEE-001",
        fee_type="application_fee",
        fee_name="Application Fee",
        amount=Decimal("250"),
        is_percentage=False,
        is_capitalised=True,
        is_waivable=True,
        description="One-time application processing fee"
    ))
    
    service.add_fee_to_product(pl_standard.product_id, LoanFee(
        fee_id="FEE-002",
        fee_type="monthly_fee",
        fee_name="Monthly Account Fee",
        amount=Decimal("10"),
        is_percentage=False,
        is_capitalised=False,
        is_waivable=False,
        description="Monthly account maintenance fee"
    ))
    
    products.append(pl_standard)
    
    # 2. Car Loan
    car_loan = service.create_product(CreateLoanProductRequest(
        product_code="CAR-SECURED-001",
        product_name="Car Loan - Secured",
        product_type=LoanProductType.CAR,
        description="Secured car loan with competitive rates",
        min_loan_amount=Decimal("10000"),
        max_loan_amount=Decimal("100000"),
        min_term_months=12,
        max_term_months=84,
        default_term_months=60,
        base_interest_rate=Decimal("0.0650"),  # 6.50%
        rate_type=InterestRateType.FIXED,
        allowed_repayment_frequencies=["monthly", "fortnightly"],
        default_repayment_frequency="monthly",
        amortization_type="principal_and_interest",
        requires_security=True,
        created_by="system"
    ))
    
    products.append(car_loan)
    
    # 3. Home Loan - Variable
    home_loan = service.create_product(CreateLoanProductRequest(
        product_code="HOME-VAR-001",
        product_name="Home Loan - Variable Rate",
        product_type=LoanProductType.HOME,
        description="Variable rate home loan with offset account",
        min_loan_amount=Decimal("100000"),
        max_loan_amount=Decimal("2000000"),
        min_term_months=60,
        max_term_months=360,
        default_term_months=300,
        base_interest_rate=Decimal("0.0550"),  # 5.50%
        rate_type=InterestRateType.VARIABLE,
        allowed_repayment_frequencies=["monthly"],
        default_repayment_frequency="monthly",
        amortization_type="principal_and_interest",
        requires_security=True,
        created_by="system"
    ))
    
    products.append(home_loan)
    
    # 4. Green Loan
    green_loan = service.create_product(CreateLoanProductRequest(
        product_code="GREEN-001",
        product_name="Green Loan - Sustainable Living",
        product_type=LoanProductType.GREEN,
        description="Discounted rate for solar, EV, and energy efficiency",
        min_loan_amount=Decimal("5000"),
        max_loan_amount=Decimal("50000"),
        min_term_months=12,
        max_term_months=84,
        default_term_months=60,
        base_interest_rate=Decimal("0.0599"),  # 5.99% (discounted)
        rate_type=InterestRateType.FIXED,
        allowed_repayment_frequencies=["monthly", "fortnightly"],
        default_repayment_frequency="monthly",
        amortization_type="principal_and_interest",
        requires_security=False,
        created_by="system"
    ))
    
    products.append(green_loan)
    
    return products
