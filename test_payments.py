"""
Test OpenAI Payment System
"""
import asyncio
import sys
import os

# Fix API key loading FIRST
with open('.env', 'r') as f:
    for line in f:
        if 'OPENAI_API_KEY=' in line:
            key = line.split('=')[1].strip()
            os.environ['OPENAI_API_KEY'] = key
            print(f"Loaded API key: {key[:30]}...")
            break

sys.path.insert(0, 'src')

# from ultracore.payments.payment_system import UltraCorePaymentSystem  # TODO: Fix import path

async def main():
    print("\n?? ULTRACORE OPENAI PAYMENT SYSTEM TEST")
    print("="*60)
    
    # Initialize system
    system = UltraCorePaymentSystem()
    
    # Test various scenarios
    test_scenarios = [
        "What can you help me with?",
        "Check my account balance",
        "Send $500 to John Smith at 0412345678",
        "Analyze the risk of sending $25000 internationally",
        "Pay my electricity bill for $234.50",
        "What's the status of payment PAY20240101123456?"
    ]
    
    print("\nRunning test scenarios...\n")
    
    for scenario in test_scenarios:
        print(f"?? User: {scenario}")
        response = await system.process_single_request(scenario)
        print(f"?? Assistant: {response[:200]}..." if len(response) > 200 else f"?? Assistant: {response}")
        print("-"*40)
    
    print("\n? All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
