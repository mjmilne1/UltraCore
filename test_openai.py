import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or api_key == "sk-your-api-key-here":
    print("? OpenAI API key not set!")
    print("Please add your key to .env file")
else:
    print(f"? OpenAI API key configured: {api_key[:10]}...")
    
    # Test the API with new syntax
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"? API test successful: {response.choices[0].message.content}")
    except Exception as e:
        print(f"? API test failed: {e}")
