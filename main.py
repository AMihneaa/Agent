from agent.agent import AIAgent
from dotenv import load_dotenv
import os
import asyncio

async def main():
    API_LM_KEY = os.getenv("API_LM_KEY")
    print(API_LM_KEY)
    agent = AIAgent(API_LM_KEY)
    
    await agent.chat()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())

    