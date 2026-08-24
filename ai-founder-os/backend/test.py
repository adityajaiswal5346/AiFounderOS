import os
import sys
import asyncio
from pathlib import Path

# Step 1: Ensure the backend directory is in the path
backend_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(backend_dir))

# Step 2: Load environment variables just like the app does
from dotenv import load_dotenv
repo_root = backend_dir.parent
load_dotenv(repo_root / ".env")

from llm.provider import get_model

async def test_llm():
    print("=" * 50)
    print("AI Founder OS — LLM Connection Test")
    print("=" * 50)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        # Show first 5 and last 5 characters securely
        masked_key = f"{api_key[:5]}...{api_key[-5:]}"
        print(f"[+] GOOGLE_API_KEY detected: {masked_key}")
    else:
        print("[-] GOOGLE_API_KEY is NOT SET. Please check your .env file.")
        return

    print("\n[~] Connecting to Gemini API...")
    
    try:
        model = get_model()
        response = await model.ainvoke("Write a beautiful poem about building AI agents. It should be exactly 100 words long.")
        print("\n[+] API Call Successful!")
        print(f"\n[+] Model Reply:\n\n{response.content}\n")
        
    except Exception as e:
        print("\n[-] API Call Failed!")
        print(f"[-] Error Details: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
