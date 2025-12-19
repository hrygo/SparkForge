import os
import asyncio
from llm import LLMClient

async def main():
    # Make sure you have API keys set in your environment
    # os.environ["OPENAI_API_KEY"] = "your-key"
    # os.environ["DEEPSEEK_API_KEY"] = "your-key"
    
    client = LLMClient()
    
    print("--- Testing OpenAI (Sync) ---")
    try:
        resp = client.chat(
            messages=[{"role": "user", "content": "Hello, who are you?"}],
            provider="openai"
        )
        print(f"Response: {resp.content}\n")
    except Exception as e:
        print(f"OpenAI error: {e}\n")

    print("--- Testing DeepSeek (Async) ---")
    try:
        resp = await client.achat(
            messages=[{"role": "user", "content": "What is the capital of France?"}],
            provider="deepseek"
        )
        print(f"Response: {resp.content}\n")
    except Exception as e:
        print(f"DeepSeek error: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
