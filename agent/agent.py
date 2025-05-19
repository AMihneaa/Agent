import json
import httpx
import os
from dotenv import load_dotenv
from agent.tool_function import calculateFunc, scrapWeatherFunc, crawlSubjectFunc
from agent.tool import tools, tool_functions
import inspect

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
            "tool-chain": "none"
        }
        self.executed_calls = set()

    def system_prompt(self):
        return (
            "Your job is to always use available tools to answer questions about:\n"
            "- Math: use `calculateFunc`\n"
            "- Weather: use `scrapWeatherFunc`\n"
            "- Public topics, events, people, or anything Wikipedia-related: use `crawlSubjectFunc`\n"
            "- ONLY CALL THE FUNCTION 1 TIME"
            "\n"
            "- ONLY CALL A TOOL ONCE with the same input. If you've already called it with specific arguments, do not call it again.\n"
            "- Only call the same tool again if the input arguments are DIFFERENT from any previous calls.\n"
            "- DO NOT answer by yourself if a tool exists.\n"
            "- DO NOT say you don't know before calling the tool first.\n"
            "- DO NOT guess answers.\n"
            "You MUST always call crawlSubjectFunc when the user asks about a person, concept, job, public figure, or country leader.\n"
            "\n"
            "When calling crawlSubjectFunc:\n"
            "  * You MUST include BOTH `subject` and `start_url` in your function call. Never include only subject. Both are REQUIRED.\n"
            "  * Translate the subject to English before calling the function.\n"
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

                while "tool_calls" in message:
                    tool_messages = []
                    for call in message["tool_calls"]:
                        tool_name = call["function"]["name"]
                        raw_args = call["function"]["arguments"]

                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError as e:
                            print(f"[ERROR] JSON decode error: {e}")
                            continue

                        call_key = (tool_name, json.dumps(args, sort_keys=True))
                        if call_key in self.executed_calls:
                            print(f"[SKIP] Duplicate tool call: {tool_name} with same arguments")
                            continue

                        self.executed_calls.add(call_key)

                        func = tool_functions.get(tool_name)
                        if not func:
                            result = f"Unknown tool: {tool_name}"
                        elif inspect.iscoroutinefunction(func):
                            result = await func(**args)
                        else:
                            result = func(**args)

                        tool_messages.append({
                            "role": "tool",
                            "tool_call_id": call["id"],
                            "name": tool_name,
                            "content": result
                        })

                    self.payload["messages"].extend(tool_messages)
                    follow_up = await client.post(self.url, json=self.payload)
                    message = follow_up.json()["choices"][0]["message"]
                    self.payload["messages"].append(message)

                if "content" in message:
                    print("Model:", message["content"])
                elif "tool_calls" not in message:
                    print("[WARN] No 'content' or 'tool_calls' in message:", message)
