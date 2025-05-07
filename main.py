from agent.__init__ import AIAgent
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv()

    API_LM_KEY = os.getenv("API_LM_KEY")
    agent = AIAgent(API_LM_KEY)
    
    agent.chat()