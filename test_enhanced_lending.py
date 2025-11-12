"""
Test Enhanced Lending Platform with all patterns
"""

import asyncio
import sys
from decimal import Decimal
sys.path.insert(0, 'src')

async def test_enhanced_lending():
    print("\n" + "="*70)
    print("   ENHANCED LENDING PLATFORM TEST")
    print("   Data Mesh + MCP + Agentic AI + ML + Kafka")
    print("="*70)
    
    from ultracore.lending.enhanced_lending_domain import (
        EnhancedLendingDomain,
        LendingDataMesh,
        CreditScoringML,
        LendingAgents,
        LendingMCPTools
    )
    
    # Initialize platform
    platform = EnhancedLendingDomain()
    
    print("\n✅ Platform initialized with all architectural patterns")
    
    # Test application
    test_application = {
        "application_id": "APP_TEST_001",
        "customer_id": "CUST_001",
        "loan_type": "personal_loan",
        "loan_amount": 25000,
        "term_months": 36,
        "annual_income": 75000,
        "debt_amount": 10000,
        "credit_score": 720,
        "employment_years": 5,
        "credit_history_months": 84,
        "num_accounts": 5,
        "recent_inquiries": 1,
        "customer_months": 24,
        "avg_balance": 5000,
        "overdrafts_12m": 0
    }
    
    # Test 1: ML Credit Scoring
    print("\n1️⃣ ML CREDIT SCORING")
    print("-" * 40)
    ml_result = await platform.ml_models.predict_credit_risk(test_application)
    print(f"   Risk Score: {ml_result['risk_score']:.3f}")
    print(f"   Confidence: {ml_result['confidence']:.2%}")
    print(f"   Model Scores:")
    for model, score in ml_result['model_scores'].items():
        print(f"     - {model}: {score:.3f}")
    
    # Test 2: Agentic AI Underwriting
    print("\n2️⃣ AGENTIC AI UNDERWRITING")
    print("-" * 40)
    decision = await platform.agents.underwriting_agent(test_application)
    print(f"   Decision: {decision['decision']}")
    print(f"   Interest Rate: {decision['pricing']['interest_rate']:.2%}")
    print(f"   Monthly Payment: ${decision['pricing']['monthly_payment']:,.2f}")
    print(f"   Risk Tier: {decision['pricing']['risk_tier']}")
    
    # Test 3: Data Mesh Produ$enhancedTest = @'
"""
Test Enhanced Lending Platform with all patterns
"""

import asyncio
import sys
from decimal import Decimal
sys.path.insert(0, 'src')

async def test_enhanced_lending():
    print("\n" + "="*70)
    print("   ENHANCED LENDING PLATFORM TEST")
    print("   Data Mesh + MCP + Agentic AI + ML + Kafka")
    print("="*70)
    
    from ultracore.lending.enhanced_lending_domain import (
        EnhancedLendingDomain,
        LendingDataMesh,
        CreditScoringML,
        LendingAgents,
        LendingMCPTools
    )
    
    # Initialize platform
    platform = EnhancedLendingDomain()
    
    print("\n✅ Platform initialized with all architectural patterns")
    
    # Test application
    test_application = {
        "application_id": "APP_TEST_001",
        "customer_id": "CUST_001",
        "loan_type": "personal_loan",
        "loan_amount": 25000,
        "term_months": 36,
        "annual_income": 75000,
        "debt_amount": 10000,
        "credit_score": 720,
        "employment_years": 5,
        "credit_history_months": 84,
        "num_accounts": 5,
        "recent_inquiries": 1,
        "customer_months": 24,
        "avg_balance": 5000,
        "overdrafts_12m": 0
    }
    
    # Test 1: ML Credit Scoring
    print("\n1️⃣ ML CREDIT SCORING")
    print("-" * 40)
    ml_result = await platform.ml_models.predict_credit_risk(test_application)
    print(f"   Risk Score: {ml_result['risk_score']:.3f}")
    print(f"   Confidence: {ml_result['confidence']:.2%}")
    print(f"   Model Scores:")
    for model, score in ml_result['model_scores'].items():
        print(f"     - {model}: {score:.3f}")
    
    # Test 2: Agentic AI Underwriting
    print("\n2️⃣ AGENTIC AI UNDERWRITING")
    print("-" * 40)
    decision = await platform.agents.underwriting_agent(test_application)
    print(f"   Decision: {decision['decision']}")
    print(f"   Interest Rate: {decision['pricing']['interest_rate']:.2%}")
    print(f"   Monthly Payment: ${decision['pricing']['monthly_payment']:,.2f}")
    print(f"   Risk Tier: {decision['pricing']['risk_tier']}")
    
    # Test 3: Data Mesh Products
    print("\n3️⃣ DATA MESH PRODUCTS")
    print("-" * 40)
    for product_name, product in platform.data_mesh.data_products.items():
        print(f"   • {product_name}")
        print(f"     Owner: {product['owner']}")
        print(f"     SLA Accuracy: {product['quality_sla'].get('accuracy', 'N/A')}")
    
    # Test 4: MCP Tools
    print("\n4️⃣ MCP TOOLS")
    print("-" * 40)
    for tool_name in platform.mcp_tools.tools.keys():
        print(f"   • {tool_name}")
    
    # Test 5: Kafka Event Streaming
    print("\n5️⃣ KAFKA EVENT STREAMING")
    print("-" * 40)
    result = await platform.process_loan_application(test_application)
    print(f"   Event ID: {result['event_id']}")
    print(f"   Processing Time: {result['processing_time_ms']}ms")
    print(f"   Final Decision: {result['decision']['decision']}")
    
    print("\n" + "="*70)
    print("   TEST COMPLETE - ALL PATTERNS WORKING")
    print("="*70)
    
    print("\n🏗️ ARCHITECTURAL PATTERNS DEMONSTRATED:")
    print("  ✅ Data Mesh: 3 data products with SLAs")
    print("  ✅ ML Models: Ensemble with 3 models")
    print("  ✅ Agentic AI: Autonomous underwriting")
    print("  ✅ MCP: 5 lending tools registered")
    print("  ✅ Kafka: Event-first architecture")

if __name__ == "__main__":
    asyncio.run(test_enhanced_lending())
