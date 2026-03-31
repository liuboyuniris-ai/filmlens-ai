import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)
api_key = os.getenv("LLM_API_KEY")
model_id = os.getenv("LLM_MODEL", "gemini-2.0-flash")

async def check_quota():
    client = genai.Client(api_key=api_key)
    target_model = "gemini-2.5-flash"
    print(f"Attempting content generation with STABLE model: {target_model}...")
    try:
        response = client.models.generate_content(
            model=target_model,
            contents="Hi, this is a stability check."
        )
        print(f"SUCCESS! Response: {response.text}")
    except Exception as e:
        print(f"Stability check failed: {e}")
        
        # Check if we can see headers or more info
        if hasattr(e, 'response'):
            print(f"Status Code: {e.response.status_code}")
            print(f"Headers: {e.response.headers}")

if __name__ == "__main__":
    asyncio.run(check_quota())
