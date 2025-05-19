import httpx
import json
import asyncio
import os
from dotenv import load_dotenv
from crawler.__init__ import Crawler

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
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculateFunc",
                    "description": "Evaluate basic math expressions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {"type": "string"}
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrapWeatherFunc",
                    "description": "Fetch weather data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_name": {"type": "string"},
                            "day": {"type": "string"},
                            "degreesType": {"type": "string"}
                        },
                        "required": ["city_name", "day", "degreesType"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "crawlSubjectFunc",
                    "description": "Crawl Wikipedia for a subject.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_url": {"type": "string"},
                            "subject": {"type": "string"}
                        },
                        "required": ["start_url", "subject"]
                    }
                }
            }
        ]

    def calculateFunc(self, expression: str) -> str:
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:
            return f"Error: {e}"

    async def scrapWeatherFunc(self, city_name: str, day: str, degreesType: str) -> str:
        units = "metric" if degreesType.lower() == "celsius" else "imperial"
        load_dotenv(dotenv_path="../.env")
        api_key = os.getenv("API_KEY_METHEO")
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units={units}&appid={api_key}"

        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(weather_url)
                if res.status_code != 200:
                    return f"Failed to retrieve weather. Status code: {res.status_code}"
                data = res.json()
                temp = data['main']['temp']
                condition = data['weather'][0]['description']
                degree_label = "Celsius" if units == "metric" else "Fahrenheit"
                return f"The weather in {city_name} {day.lower()} is {temp} {degree_label}, {condition}"
            except Exception as e:
                return f"Error: {e}"

    async def async_find_wikipedia_page(self, subject: str) -> str | None:
        api_url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": subject,
            "format": "json",
            "utf8": 1
        }
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.get(api_url, params=params)
                data = res.json()
                if "query" in data and data["query"]["search"]:
                    best_match = data["query"]["search"][0]["title"]
                    return f"https://en.wikipedia.org/wiki/{best_match.replace(' ', '_')}"
                return None
        except Exception as e:
            print(f"[!] Wikipedia search error: {e}")
            return None

    async def is_valid_wikipedia_page(self, url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return False
                content = res.text.lower()
                if "wikipedia does not have an article with this exact name" in content:
                    return False
                return True
        except Exception as e:
            print(f"[!] Error checking Wikipedia page validity: {e}")
            return False

    async def crawlSubjectFunc(self, start_url: str, subject: str) -> str:
        if not start_url.startswith("http"):
            start_url = f"https://en.wikipedia.org/wiki/{start_url.replace(' ', '_')}"

        if not start_url or not await self.is_valid_wikipedia_page(start_url):
            corrected_url = await self.async_find_wikipedia_page(subject)
            if not corrected_url or not await self.is_valid_wikipedia_page(corrected_url):
                return f"[TOOL_RESULT]Could not find a valid Wikipedia page for subject: '{subject}'[END_TOOL_RESULT]"
            start_url = corrected_url

        crawler = Crawler(start_url, subject=subject)
        await crawler.multi_crawler_async(start_url, max_depth=1, tolerant_depth=1)

        results = crawler.results 
        if not results:
            return f"[TOOL_RESULT]No information found about '{subject}'.[END_TOOL_RESULT]"

        first = results[0]
        crawler.save_links_to_json("linksJson.json")
        return f"[TOOL_RESULT]{first['title']} ({first['url']})\nSnippet: {first['snippet'] if first['snippet'] else 'No description.'}[END_TOOL_RESULT]"

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
                    print(f"[DEBUG] tool_calls: {json.dumps(message['tool_calls'], indent=2)}")

                    while True:
                        tool_messages = []
                        for call in message["tool_calls"]:
                            print("Model wants to call a tool")
                            tool_name = call["function"]["name"]

                            raw_args = call["function"]["arguments"]
                            print(f"[RAW ARGS] {raw_args}")

                            try:
                                args = json.loads(raw_args)

                                if (tool_name, json.dumps(args, sort_keys=True)) in self.executed_calls:
                                    print("[INFO] Duplicate tool call blocked.")
                                    continue

                                self.executed_calls.add((tool_name, json.dumps(args, sort_keys=True)))
                            except json.JSONDecodeError as e:
                                print(f"[!] JSON decode error: {e}")
                                continue

                            if tool_name == "calculateFunc":
                                result = self.calculateFunc(args.get("expression", ""))
                            elif tool_name == "scrapWeatherFunc":
                                result = await self.scrapWeatherFunc(
                                    args.get("city_name", ""),
                                    args.get("day", ""),
                                    args.get("degreesType", "")
                                )
                            elif tool_name == "crawlSubjectFunc":
                                subject = args.get("subject")
                                start_url = args.get("start_url")
                                if not subject:
                                    result = "Missing subject for crawlSubjectFunc."
                                else:
                                    if not start_url:
                                        start_url = f"https://en.wikipedia.org/wiki/{subject.replace(' ', '_')}"
                                    print(f"[TOOL] crawlSubjectFunc called with subject='{subject}' and start_url='{start_url}'")
                                    result = await self.crawlSubjectFunc(start_url, subject)
                            else:
                                result = f"Unknown tool: {tool_name}"

                            tool_messages.append({
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "name": tool_name,
                                "content": result
                            })

                        self.payload["messages"].extend(tool_messages)
                        res2 = await client.post(self.url, json=self.payload)
                        follow_up = res2.json()["choices"][0]["message"]

                        if "content" in follow_up:
                            print("Model:", follow_up["content"])
                            self.payload["messages"].append(follow_up)
                            break
                        elif "tool_calls" in follow_up:
                            print("Model wants to call another function again.")
                            message = follow_up 
                            self.payload["messages"].append(follow_up)

                elif "content" in message:
                    print("Model:", message["content"])
                    self.payload["messages"].append(message)

