import json
import httpx
import os
from dotenv import load_dotenv
from agent.tool_function import calculateFunc, scrapWeatherFunc, crawlSubjectFunc
from agent.tool import tools

class AIAgent:
    def __init__(self, url: str):
        self.url = url
        self.payload = {
            "model": "lmstudio-community/DeepSeek-R1-Distill-Qwen-7B-GGUF",
            "messages": [
                {"role": "system", "content": self.system_prompt()}
            ],
            "temperature": 0.6,
            "max_tokens": 1024,
            "tools": self.define_tools(),
            "tool-chain": "auto"
        }
        self.executed_calls = set()

    def system_prompt(self):
        return (
            "You are a helpful and strict AI agent.\n"
            "\n"
            "Your job is to always use available tools to answer questions about:\n"
            "- Math: use `calculateFunc`\n"
            "- Weather: use `scrapWeatherFunc`\n"
            "- Public topics, events, people, or anything Wikipedia-related: use `crawlSubjectFunc`\n"
            "\n"
            "YOU MUST NOT try to answer yourself when a tool exists.\n"
            "YOU MUST NOT assume the answer is unknown without calling the tool.\n"
            "You MUST always call crawlSubjectFunc when the user asks about a person, concept, job, public figure, or country leader.\n"
            "\n"
            "When calling crawlSubjectFunc:\n"
            "  * You MUST include BOTH `subject` and `start_url` in your function call. Never include only subject. Both are REQUIRED.\n"
            "  * For example: question = 'Who is the X?' → subject = 'x', start_url = 'https://en.wikipedia.org/wiki/x'\n"
            "- Always infer `subject` from the user's question.\n"
            "- Set `start_url` to 'https://en.wikipedia.org/wiki/' + subject with spaces replaced by underscores.\n"
            "- Do not skip tool call even if topic seems unusual or recent. Wikipedia likely has the info.\n"
            "- Never think 'I don't know'. Try first. Fail only after crawlSubjectFunc returns nothing.\n"
            "\n"
            "NEVER respond with 'I can't help you' unless all tool calls failed.\n"
            "Your job is to ACT, not guess.\n"
        )
    
    def define_tools(self):
        return list(tools.values())

    async def chat(self):
        timeout = httpx.Timeout(connect=1000.0, read=120000.0, write=100000.0, pool=50000000.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            while True:
                user_input = input("User: ")
                if user_input.lower() in ['exit', 'quit']:
                    break

                self.payload["messages"].append({"role": "user", "content": user_input})
                res = await client.post(self.url, json=self.payload)
                message = res.json()["choices"][0]["message"]

                if "tool_calls" in message:
                    tool_messages = []
                    for call in message["tool_calls"]:
                        tool_name = call["function"]["name"]
                        args = json.loads(call["function"]["arguments"])
                        if (tool_name, json.dumps(args, sort_keys=True)) in self.executed_calls:
                            continue
                        self.executed_calls.add((tool_name, json.dumps(args, sort_keys=True)))

                        func = tools.get(tool_name)
                        if not func:
                            result = f"Unknown tool: {tool_name}"
                        elif tool_name == "calculateFunc":
                            result = func(args.get("expression", ""))
                        else:
                            result = await func(**args)

                        tool_messages.append({
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "name": tool_name,
                            "content": result
                        })

                    self.payload["messages"].extend(tool_messages)
                    follow_up = await client.post(self.url, json=self.payload)
                    follow_msg = follow_up.json()["choices"][0]["message"]
                    print("Model:", follow_msg["content"])
                    self.payload["messages"].append(follow_msg)
                else:
                    print("Model:", message["content"])
                    self.payload["messages"].append(message)