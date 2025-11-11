from openai import OpenAI

# Read key directly
api_key = None
with open('.env', 'r') as f:
    for line in f:
        if 'OPENAI_API_KEY=' in line:
            api_key = line.split('=')[1].strip()
            break

print(f"Using API key: {api_key[:30]}...")

client = OpenAI(api_key=api_key)

def process_payment_request(user_input):
    """Process payment request with OpenAI"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": "You are a payment assistant. Help users with payments, transfers, and financial queries."
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        max_tokens=200
    )
    
    return response.choices[0].message.content

# Test it
print("\n?? SIMPLE PAYMENT SYSTEM TEST")
print("="*50)

test_requests = [
    "Help me send $100 to John",
    "Check my balance",
    "Is it safe to send $10000 internationally?"
]

for request in test_requests:
    print(f"\n?? User: {request}")
    response = process_payment_request(request)
    print(f"?? Assistant: {response}")

print("\n? Simple payment system working!")
