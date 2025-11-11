"""Interactive Payment Chat"""
from openai import OpenAI
import asyncio

# Read API key
with open('.env', 'r') as f:
    for line in f:
        if 'OPENAI_API_KEY=' in line:
            api_key = line.split('=')[1].strip()

client = OpenAI(api_key=api_key)

async def chat():
    print("\n" + "="*60)
    print("?? ULTRACORE PAYMENT ASSISTANT")
    print("="*60)
    print("Type 'exit' to quit, 'help' for commands\n")
    
    conversation = []
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'exit':
            print("?? Goodbye!")
            break
        elif user_input.lower() == 'help':
            print("""
Commands:
- Send money: "Send $100 to John"
- Check balance: "What's my balance?"
- Pay bills: "Pay electricity bill"
- Risk check: "Is it safe to send $10000?"
- exit: Quit
            """)
            continue
        
        # Add to conversation
        conversation.append({"role": "user", "content": user_input})
        
        # Get response
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful payment assistant."},
                *conversation[-5:]  # Keep last 5 messages
            ],
            max_tokens=200
        )
        
        assistant_msg = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_msg})
        
        print(f"\n?? Assistant: {assistant_msg}\n")

asyncio.run(chat())
