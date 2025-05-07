from agent.__init__ import AIAgent

if __name__ == "__main__":
    agent = AIAgent("http://192.168.56.1:1234/v1/chat/completions")
    
    agent.chat()