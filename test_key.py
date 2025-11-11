import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or "YOUR" in api_key:
    print("? No valid API key found in .env")
    print("Get your key from: https://platform.openai.com/api-keys")
else:
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        print(f"? OpenAI API working! Response: {response.choices[0].message.content}")
    except Exception as e:
        if "invalid_api_key" in str(e):
            print("? Invalid API key. Get a new one from OpenAI.")
        elif "insufficient_quota" in str(e):
            print("? No credits. Add payment method at: https://platform.openai.com/account/billing")
        else:
            print(f"? Error: {e}")
