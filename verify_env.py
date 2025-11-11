import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Check API key
api_key = os.getenv("OPENAI_API_KEY", "")

if not api_key or api_key == "paste-your-actual-api-key-here":
    print("? OpenAI API key not set!")
    print("\nPlease edit .env file and add your API key")
    print("It should look like: OPENAI_API_KEY=sk-proj-xxxxx...")
    print("\nGet your key from: https://platform.openai.com/api-keys")
else:
    # Show partial key for verification (hidden for security)
    masked_key = api_key[:10] + "..." + api_key[-4:]
    print(f"? OpenAI API key is set: {masked_key}")
    
    # Show other settings
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    print(f"? Model: {model}")
    
    debug = os.getenv("DEBUG", "false")
    print(f"? Debug mode: {debug}")
    
    max_payment = os.getenv("MAX_PAYMENT_AMOUNT", "100000")
    print(f"? Max payment: ${max_payment}")
    
    print("\n?? Your .env file is properly configured!")
