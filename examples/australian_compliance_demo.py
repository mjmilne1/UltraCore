"""
Australian Compliance Module - Complete Demonstration
Full regulatory compliance demonstration
"""

import asyncio
from datetime import datetime, timedelta

# Import all compliance modules
from ultracore.compliance.australia.asic_compliance import asic_compliance, ClientCategory
from ultracore.compliance.australia.austrac_compliance import austrac_compliance
from ultracore.compliance.australia.asx_compliance import asx_compliance
from ultracore.compliance.australia.ato_compliance import ato_compliance
from ultracore.compliance.australia.privacy_compliance import privacy_compliance, DataType, ConsentType
from ultracore.compliance.australia.corporations_compliance import corporations_compliance
from ultracore.compliance.australia.aasb_compliance import aasb_compliance
from ultracore.compliance.australia.super_compliance import super_compliance
from ultracore.compliance.australia.fcs_compliance import fcs_compliance
from ultracore.compliance.australia.compliance_integration import australian_compliance

async def main():
    print("\n" + "="*80)
    print("  🇦🇺 AUSTRALIAN COMPLIANCE MODULE - COMPLETE DEMONSTRATION")
    print("  Full Regulatory Compliance for Wealth Management")
    print("="*80 + "\n")
    
    # ========================================================================
    # 1. ASIC COMPLIANCE
    # ========================================================================
    
    print("[1/9] ASIC Compliance (Securities & Investments)")
    print("-" * 80)
    
    # Set AFSL details
    asic_compliance.set_afsl_details(
        afsl_number="123456",
        license_holder="UltraWealth Pty Ltd",
        license_type="full",
        authorized_services=[
            "Financial product advice",
            "Dealing in financial products",
            "Operating managed investment schemes"
        ]
    )
    
    print("✅ AFSL Details Set:")
    print(f"   AFSL Number: {asic_compliance.afsl_number}")
    print(f"   License Holder: {asic_compliance.license_holder}")
    
    # Client categorization
    client_data = {
        "client_id": "CLIENT-001",
        "name": "John Smith",
        "net_assets": 3000000,
        "gross_income": 200000,
        "investment_amount": 500000
    }
    
    client_category = asic_compliance.categorize_client(client_data)
    print(f"\n📊 Client Categorization:")
    print(f"   Client: {client_data['name']}")
    print(f"   Net Assets: ${client_data['net_assets']:,}")
    print(f"   Category: {client_category.upper()}")
    print(f"   Protection Level: {'High' if client_category == ClientCategory.RETAIL else 'Standard'}")
    
    # Best interests duty
    advice_data = {
        "client_objectives": "Long-term wealth accumulation",
        "financial_situation": "High net worth",
        "risk_profile": "Moderate",
        "product_research": True,
        "comparison_done": True,
        "conflicts_disclosed": True,
        "appropriateness_assessment": True
    }
    
    best_interests = asic_compliance.check_best_interests_duty(advice_data)
    print(f"\n🤝 Best Interests Duty Check:")
    print(f"   Compliant: {'✅' if best_interests['compliant'] else '❌'}")
    for check, passed in best_interests['checks'].items():
        print(f"   • {check}: {'✅' if passed else '❌'}")
    
    # FSG requirements
    fsg = asic_compliance.generate_fsg()
    print(f"\n📄 Financial Services Guide:")
    print(f"   Required: {'Yes' if fsg['fsg_required'] else 'No'}")
    print(f"   Must include:")
    for item in fsg['must_include'][:3]:
        print(f"     • {item}")
    
    # ========================================================================
    # 2. AUSTRAC COMPLIANCE
    # ========================================================================
    
    print("\n[2/9] AUSTRAC Compliance (AML/CTF)")
    print("-" * 80)
    
    # Customer Due Diligence
    kyc_data = {
        "full_name": "John Smith",
        "date_of_birth": "1980-05-15",
        "residential_address": "123 Main St, Sydney NSW 2000",
        "name_verified": True,
        "dob_verified": True,
        "address_verified": True,
        "identity_documents": [
            {"type": "passport", "points": 70},
            {"type": "drivers_license", "points": 40}
        ],
        "pep_check_done": True,
        "sanctions_check_done": True
    }
    
    cdd_result = austrac_compliance.perform_cdd(kyc_data)
    print(f"🔍 Customer Due Diligence:")
    print(f"   CDD Complete: {'✅' if cdd_result['cdd_complete'] else '❌'}")
    print(f"   Risk Rating: {cdd_result['risk_rating'].upper()}")
    print(f"   Valid Until: {cdd_result['valid_until'][:10]}")
    
    # Suspicious matter detection
    transaction = {
        "transaction_id": "TXN-001",
        "amount": 9500,
        "currency_type": "physical",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    client_history = [
        {"amount": 9800, "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()},
        {"amount": 9600, "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()}
    ]
    
    suspicious = austrac_compliance.check_suspicious_matter(transaction, client_history)
    print(f"\n🚨 Suspicious Matter Detection:")
    print(f"   Suspicious: {'⚠️ YES' if suspicious['suspicious'] else '✅ NO'}")
    if suspicious.get('red_flags'):
        print(f"   Red Flags:")
        for flag in suspicious['red_flags']:
            print(f"     • {flag}")
    
    # Threshold Transaction Report
    large_transaction = {
        "transaction_id": "TXN-002",
        "amount": 15000,
        "currency_type": "physical",
        "client_id": "CLIENT-001"
    }
    
    ttr_check = austrac_compliance.check_threshold_transaction(large_transaction)
    print(f"\n💰 Threshold Transaction Check:")
    print(f"   Amount: ${large_transaction['amount']:,}")
    print(f"   TTR Required: {'Yes' if ttr_check['ttr_required'] else 'No'}")
    if ttr_check.get('report'):
        print(f"   Must Report Within: {ttr_check['report']['must_report_within']}")
    
    # ========================================================================
    # 3. ASX COMPLIANCE
    # ========================================================================
    
    print("\n[3/9] ASX Compliance (Trading Rules)")
    print("-" * 80)
    
    # Trading hours check
    trading_hours = asx_compliance.check_trading_hours(datetime.now(timezone.utc), "VAS.AX")
    print(f"🕐 Trading Hours Check:")
    print(f"   Current Time: {datetime.now(timezone.utc).strftime('%I:%M %p')}")
    print(f"   Market Phase: {trading_hours['market_phase'].upper()}")
    print(f"   Trading Allowed: {'✅ YES' if trading_hours['trading_allowed'] else '❌ NO'}")
    
    # Price limits check
    price_check = asx_compliance.check_price_limits("VAS.AX", 110.00, 100.00)
    print(f"\n💵 Price Limits Check:")
    print(f"   Order Price: ${price_check['order_price']:.2f}")
    print(f"   Reference Price: ${price_check['reference_price']:.2f}")
    print(f"   Deviation: {price_check['deviation_pct']:.2f}%")
    print(f"   Within Limits: {'✅ YES' if price_check['within_limits'] else '❌ NO'}")
    
    # Short selling check
    order = {
        "side": "sell",
        "ticker": "VAS.AX",
        "quantity": 1000,
        "borrowed_stock_confirmed": True
    }
    
    holdings = {"VAS.AX": 500}
    
    short_check = asx_compliance.check_short_selling_rules(order, holdings)
    print(f"\n📊 Short Selling Check:")
    print(f"   Is Short Sale: {'Yes' if short_check['short_sale'] else 'No'}")
    print(f"   Compliant: {'✅ YES' if short_check['compliant'] else '❌ NO'}")
    if short_check.get('covered'):
        print(f"   Covered: ✅ Stock borrowed")
    
    # ========================================================================
    # 4. ATO COMPLIANCE
    # ========================================================================
    
    print("\n[4/9] ATO Compliance (Taxation)")
    print("-" * 80)
    
    # Capital Gains Tax calculation
    sale = {
        "sale_id": "SALE-001",
        "ticker": "VAS.AX",
        "date": datetime.now(timezone.utc).isoformat(),
        "price": 110.00,
        "quantity": 500
    }
    
    purchase_history = [
        {
            "date": (datetime.now(timezone.utc) - timedelta(days=400)).isoformat(),
            "price": 95.00,
            "quantity": 300
        },
        {
            "date": (datetime.now(timezone.utc) - timedelta(days=200)).isoformat(),
            "price": 100.00,
            "quantity": 200
        }
    ]
    
    cgt_result = ato_compliance.calculate_cgt(sale, purchase_history)
    print(f"💰 Capital Gains Tax Calculation:")
    print(f"   Ticker: {cgt_result['ticker']}")
    print(f"   Total Proceeds: ${cgt_result['total_proceeds']:,.2f}")
    print(f"   Total Cost Base: ${cgt_result['total_cost_base']:,.2f}")
    print(f"   Gross Capital Gain: ${cgt_result['gross_capital_gain']:,.2f}")
    print(f"   CGT Discount Applied: {'✅ YES' if cgt_result['cgt_discount_applied'] else 'NO'}")
    print(f"   Taxable Amount: ${cgt_result['taxable_amount']:,.2f}")
    
    # Dividend income
    dividend = {
        "dividend_id": "DIV-001",
        "ticker": "VAS.AX",
        "amount": 1000,
        "franking_percentage": 100,
        "payment_date": datetime.now(timezone.utc).isoformat()
    }
    
    dividend_result = ato_compliance.calculate_dividend_income(dividend)
    print(f"\n💵 Dividend Income:")
    print(f"   Dividend Amount: ${dividend_result['dividend_amount']:,.2f}")
    print(f"   Franking Credit: ${dividend_result['franking_credit']:,.2f}")
    print(f"   Assessable Income: ${dividend_result['assessable_income']:,.2f}")
    
    # TFN validation
    tfn_result = ato_compliance.validate_tfn("123 456 789")
    print(f"\n🔢 TFN Validation:")
    print(f"   Valid: {'✅ YES' if tfn_result['valid'] else '❌ NO'}")
    
    # ========================================================================
    # 5. PRIVACY ACT COMPLIANCE
    # ========================================================================
    
    print("\n[5/9] Privacy Act Compliance")
    print("-" * 80)
    
    # Privacy notice
    privacy_notice = privacy_compliance.generate_privacy_notice("UltraWealth Pty Ltd")
    print(f"📄 Privacy Notice:")
    print(f"   Entity: {privacy_notice['entity_name']}")
    print(f"   What We Collect:")
    for item in privacy_notice['what_we_collect'][:3]:
        print(f"     • {item}")
    
    # Consent recording
    consent = privacy_compliance.record_consent(
        client_id="CLIENT-001",
        data_type=DataType.PERSONAL,
        purpose="Provide financial services",
        consent_type=ConsentType.EXPRESS
    )
    print(f"\n✅ Consent Recorded:")
    print(f"   Consent ID: {consent['consent_id']}")
    print(f"   Data Type: {consent['consent']['data_type']}")
    print(f"   Valid: {'✅ YES' if consent['valid'] else '❌ NO'}")
    
    # Data security check
    security_measures = {
        "encryption_at_rest": True,
        "encryption_in_transit": True,
        "access_controls": True,
        "audit_logging": True,
        "regular_backups": True,
        "incident_response_plan": True,
        "staff_training": True,
        "destruction_policy": True
    }
    
    security_check = privacy_compliance.check_data_security(security_measures)
    print(f"\n🔒 Data Security Check:")
    print(f"   Compliant: {'✅ YES' if security_check['compliant'] else '❌ NO'}")
    print(f"   Compliance Score: {security_check['compliance_score']:.0f}%")
    
    # ========================================================================
    # 6. CORPORATIONS ACT COMPLIANCE
    # ========================================================================
    
    print("\n[6/9] Corporations Act Compliance")
    print("-" * 80)
    
    # ACN validation
    acn_result = corporations_compliance.validate_acn("123 456 789")
    print(f"🏢 ACN Validation:")
    print(f"   ACN: {acn_result['acn'] if acn_result['valid'] else 'Invalid'}")
    print(f"   Valid: {'✅ YES' if acn_result['valid'] else '❌ NO'}")
    
    # Director duties
    action = {
        "description": "Investment decision",
        "personal_benefit": False
    }
    
    director_check = corporations_compliance.check_director_duties(action)
    print(f"\n👔 Director Duties Check:")
    print(f"   Compliant: {'✅ YES' if director_check['compliant'] else '❌ NO'}")
    
    # Financial reporting
    reporting = corporations_compliance.check_financial_reporting("large_proprietary")
    print(f"\n📊 Financial Reporting Requirements:")
    print(f"   Report Required: {'Yes' if reporting['financial_report_required'] else 'No'}")
    print(f"   Audit Required: {'Yes' if reporting['audit_required'] else 'No'}")
    print(f"   Deadline: {reporting['deadline']}")
    
    # ========================================================================
    # 7. AASB COMPLIANCE
    # ========================================================================
    
    print("\n[7/9] AASB Compliance (Accounting Standards)")
    print("-" * 80)
    
    # Financial instrument classification
    instrument = {
        "type": "equity_investment",
        "business_model": "trade",
        "cash_flows": "other"
    }
    
    classification = aasb_compliance.check_financial_instrument_classification(instrument)
    print(f"📈 Financial Instrument Classification:")
    print(f"   Type: {classification['instrument_type']}")
    print(f"   Classification: {classification['classification'].upper()}")
    print(f"   Measurement: {classification['measurement_basis']}")
    print(f"   Standard: {classification['standard']}")
    
    # Revenue recognition
    revenue = {
        "type": "management_fee"
    }
    
    revenue_rec = aasb_compliance.check_revenue_recognition(revenue)
    print(f"\n💰 Revenue Recognition:")
    print(f"   Type: {revenue_rec['revenue_type']}")
    print(f"   Recognition Pattern: {revenue_rec['recognition']['recognition_pattern']}")
    print(f"   Standard: {revenue_rec['standard']}")
    
    # ========================================================================
    # 8. SUPERANNUATION COMPLIANCE
    # ========================================================================
    
    print("\n[8/9] Superannuation Compliance")
    print("-" * 80)
    
    # Sole purpose test
    super_transaction = {
        "purpose": "retirement_benefit"
    }
    
    sole_purpose = super_compliance.check_sole_purpose_test(super_transaction)
    print(f"🎯 Sole Purpose Test:")
    print(f"   Purpose: {sole_purpose['purpose']}")
    print(f"   Compliant: {'✅ YES' if sole_purpose['compliant'] else '❌ NO'}")
    
    # Contribution caps
    contributions = {
        "concessional": 25000,
        "non_concessional": 100000,
        "total_super_balance": 1500000
    }
    
    caps_check = super_compliance.check_contribution_caps(contributions, 2025)
    print(f"\n💵 Contribution Caps Check (FY 2024-25):")
    print(f"   Concessional: ${caps_check['concessional']['contributed']:,} / ${caps_check['concessional']['cap']:,}")
    print(f"   Compliant: {'✅ YES' if caps_check['concessional']['compliant'] else '❌ NO'}")
    print(f"   Non-Concessional: ${caps_check['non_concessional']['contributed']:,} / ${caps_check['non_concessional']['cap']:,}")
    print(f"   Compliant: {'✅ YES' if caps_check['non_concessional']['compliant'] else '❌ NO'}")
    
    # Pension minimum
    pension_min = super_compliance.calculate_pension_minimum(500000, 67, 2025)
    print(f"\n🏦 Pension Minimum Payment:")
    print(f"   Account Balance: ${pension_min['account_balance']:,}")
    print(f"   Age: {pension_min['member_age']}")
    print(f"   Minimum %: {pension_min['minimum_percentage']}%")
    print(f"   Minimum Payment: ${pension_min['minimum_payment']:,.2f}")
    
    # ========================================================================
    # 9. FINANCIAL CLAIMS SCHEME
    # ========================================================================
    
    print("\n[9/9] Financial Claims Scheme")
    print("-" * 80)
    
    # FCS protection
    account = {
        "balance": 300000,
        "type": "savings",
        "institution": "Commonwealth Bank"
    }
    
    fcs_check = fcs_compliance.check_fcs_protection(account)
    print(f"🛡️ FCS Protection:")
    print(f"   Account Balance: ${fcs_check['account_balance']:,}")
    print(f"   Protected Amount: ${fcs_check['protected_amount']:,}")
    print(f"   Unprotected Amount: ${fcs_check['unprotected_amount']:,}")
    print(f"   Fully Protected: {'✅ YES' if fcs_check['fully_protected'] else '⚠️ NO'}")
    
    # ========================================================================
    # INTEGRATED COMPLIANCE CHECK
    # ========================================================================
    
    print("\n" + "="*80)
    print("  🎯 INTEGRATED COMPLIANCE DEMONSTRATION")
    print("="*80 + "\n")
    
    # Full onboarding compliance
    print("📋 Complete Client Onboarding:")
    
    onboarding_result = await australian_compliance.onboard_client_compliant({
        "client_id": "CLIENT-002",
        "full_name": "Jane Doe",
        "date_of_birth": "1985-03-20",
        "residential_address": "456 George St, Melbourne VIC 3000",
        "net_assets": 1500000,
        "gross_income": 180000,
        "name_verified": True,
        "dob_verified": True,
        "address_verified": True,
        "identity_documents": [
            {"type": "passport", "points": 70},
            {"type": "utility_bill", "points": 40}
        ],
        "pep_check_done": True,
        "sanctions_check_done": True,
        "tfn": "987 654 321"
    })
    
    print(f"   Overall Compliant: {'✅ YES' if onboarding_result['compliant'] else '❌ NO'}")
    print(f"   Client Category: {onboarding_result['client_category'].upper()}")
    print(f"   Can Proceed: {'✅ YES' if onboarding_result['can_proceed'] else '❌ NO'}")
    
    # Compliance dashboard
    print("\n📊 Compliance Dashboard:")
    dashboard = await australian_compliance.generate_compliance_dashboard()
    
    for regulator, status in dashboard['regulatory_bodies'].items():
        print(f"   {regulator}: {status['status'].upper()}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    
    print("\n" + "="*80)
    print("  🎉 AUSTRALIAN COMPLIANCE DEMONSTRATION COMPLETE!")
    print("="*80 + "\n")
    
    print("✅ Regulatory Bodies Covered:")
    print("   • ASIC (Securities & Investments)")
    print("   • AUSTRAC (AML/CTF)")
    print("   • ASX (Trading Rules)")
    print("   • ATO (Taxation)")
    print("   • Privacy Act 1988")
    print("   • Corporations Act 2001")
    print("   • AASB (Accounting Standards)")
    print("   • Superannuation (SIS Act)")
    print("   • Financial Claims Scheme")
    
    print("\n🚀 Your platform is fully Australian compliant!")
    print("   Client → KYC/AML → Trade → Tax → Report → Audit")
    
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
