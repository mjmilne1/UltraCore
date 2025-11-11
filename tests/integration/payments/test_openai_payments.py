"""
OpenAI Payment System Test
"""
import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, 'src')

# Set your API key here for testing
# os.environ["OPENAI_API_KEY"] = "sk-your-key-here"

from ultracore.payments.openai_assistant import OpenAIPaymentAssistant
from ultracore.payments.agentic_orchestrator import AgenticPaymentOrchestrator

async def test_openai_system():
    print("\n" + "="*60)
    print("OPENAI PAYMENT SYSTEM TEST")
    print("="*60)
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "sk-your-key-here":
        print("\n??  OpenAI API key not set!")
        print("Please set OPENAI_API_KEY environment variable")
        print("Or edit this test file and add your key")
        return
    
    # Initialize
    config = {"test": True}
    orchestrator = AgenticPaymentOrchestrator(config)
    assistant = OpenAIPaymentAssistant(orchestrator)
    
    # Test
    print("\nTesting OpenAI Assistant...")
    response = await assistant.process_message("Send $100 to John")
    print(f"Response: {response}")
    
    print("\n? Test complete!")

if __name__ == "__main__":
    asyncio.run(test_openai_system())
