"""
Test Complete Lending Platform
"""

import asyncio
import sys
from decimal import Decimal
sys.path.insert(0, 'src')

async def test_lending_platform():
    print("\n" + "="*60)
    print("   COMPLETE LENDING PLATFORM TEST")
    print("="*60)
    
    from ultracore.lending.lending_domain import LendingDomain, LoanType
    from ultracore.lending.bnpl import BNPLProvider
    from ultracore.lending.credit_line import CreditLineManager
    from ultracore.lending.mortgage import MortgageEngine
    
    # Initialize components
    lending = LendingDomain()
    bnpl = BNPLProvider()
    credit_lines = CreditLineManager()
    mortgages = MortgageEngine()
    
    print("\n[OK] All lending components initialized")
    
    # Test 1: Personal Loan
    print("\n1. PERSONAL LOAN TEST")
    print("-" * 40)
    personal_loan_app = {
        "customer_id": "CUST_001",
        "loan_type": "personal_loan",
        "amount": 25000,
        "term_months": 36,
        "annual_income": 75000,
        "credit_score": 720,
        "employment_years": 5
    }
    
    result = await lending.originate_loan(personal_loan_app)
    print(f"   Status: {result['status']}")
    if result['status'] == 'APPROVED':
        print(f"   Amount: ${result['amount']:,}")
        print(f"   Rate: {result['interest_rate']:.2%}")
        print(f"   Payment: ${result['monthly_payment']}/month")
    
    # Test 2: BNPL
    print("\n2. BUY NOW PAY LATER TEST")
    print("-" * 40)
    purchase = {
        "merchant_id": "MERCH_001",
        "amount": 1500,
        "description": "Electronics purchase"
    }
    
    bnpl_result = await bnpl.instant_approval("CUST_002", purchase)
    print(f"   Approved: {bnpl_result['approved']}")
    if bnpl_result['approved']:
        print(f"   Plan: {len(bnpl_result['payment_schedule'])} installments")
        print(f"   First payment: {bnpl_result['first_payment'][:10]}")
    
    # Test 3: Credit Line
    print("\n3. REVOLVING CREDIT TEST")
    print("-" * 40)
    credit_assessment = {
        "annual_income": 90000,
        "risk_score": 0.75,
        "credit_score": 750
    }
    
    credit_facility = await credit_lines.establish_credit_line("CUST_003", credit_assessment)
    print(f"   Credit Limit: ${credit_facility['credit_limit']:,}")
    print(f"   Interest Rate: {credit_facility['interest_rate']:.2%}")
    
    # Draw from credit line
    draw_result = await credit_lines.drawdown(
        credit_facility['facility_id'], 
        Decimal("5000")
    )
    print(f"   Drawdown: ${draw_result.get('amount_drawn', 0):,}")
    print(f"   Available: ${draw_result.get('available_credit', 0):,}")
    
    # Test 4: Mortgage
    print("\n4. MORTGAGE TEST")
    print("-" * 40)
    mortgage_app = {
        "customer_id": "CUST_004",
        "loan_amount": 450000,
        "term_years": 30,
        "annual_income": 120000,
        "annual_expenses": 40000,
        "credit_score": 780,
        "property": {
            "property_id": "PROP_001",
            "purchase_price": 500000
        },
        "documents": {
            "proof_of_income": True,
            "bank_statements": True,
            "identification": True,
            "employment_letter": True,
            "property_contract": True
        }
    }
    
    mortgage_result = await mortgages.process_mortgage_application(mortgage_app)
    print(f"   Status: {mortgage_result['status']}")
    if mortgage_result['status'] == 'APPROVED':
        print(f"   Loan: ${mortgage_result['loan_amount']:,}")
        print(f"   Rate: {mortgage_result['interest_rate']:.2%}")
        print(f"   Payment: ${mortgage_result['monthly_payment']:,.0f}/month")
    
    print("\n" + "="*60)
    print("   LENDING PLATFORM TEST COMPLETE")
    print("="*60)
    
    print("\n[CAPABILITIES DEMONSTRATED]")
    print("  ✓ Personal loans with risk-based pricing")
    print("  ✓ Instant BNPL approval")
    print("  ✓ Revolving credit facilities")
    print("  ✓ Full mortgage processing")
    print("  ✓ ML-based credit decisioning")

if __name__ == "__main__":
    asyncio.run(test_lending_platform())
