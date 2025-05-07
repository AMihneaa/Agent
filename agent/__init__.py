import requests
import json
from crawler.__init__ import Crawler  
import asyncio
from dotenv import load_dotenv
import os

class AIAgent:
    def __init__(self, url: str):
        self.url = url
        self.payload = {
            "model": "lmstudio-community/DeepSeek-R1-Distill-Qwen-7B-GGUF",
            "messages": [
                {"role": "system", "content": self.system_prompt()}
            ],
            "temperature": 0.7,
            "max_tokens": 30000,
            "tools": self.define_tools(),
            "tool-chain": "auto"
        }

    def system_prompt(self):
        return (
            "You are a helpful and strict AI agent.\n"
            "\n"
            "You MUST ALWAYS use available functions to answer questions about math, weather, or content crawling.\n"
            "\n"
            "- For math expressions, always use `calculateFunc`. Do NOT think or solve math yourself.\n"
            "- For weather information, always use `scrapWeatherFunc`. Do NOT guess weather info.\n"
            "- For subject-related Wikipedia crawling, always use `crawlSubjectFunc`.\n"
            "\n"
            "- When using `crawlSubjectFunc`:\n"
           "- When using `crawlSubjectFunc`:\n"
            "  * You MUST include BOTH `subject` and `start_url` in your function call.\n"
            "  * If the user’s message refers to a person, concept, app, event, or topic:\n"
            "      -> Infer subject directly from the message.\n"
            "      -> Set start_url as: https://en.wikipedia.org/wiki/<subject_with_underscores>\n"
            "  * Do not avoid the tool just because the topic seems unusual. Assume most public concepts have Wikipedia pages.\n"
            "  * Example: 'What is TikTok?' → subject: 'TikTok', start_url: 'https://en.wikipedia.org/wiki/TikTok'\n"
            "  * If the subject cannot be converted to a URL, only then fall back to 'https://en.wikipedia.org/wiki/Main_Page'\n"
            "  * You are expected to think and apply your best guess based on public knowledge.\n"
            "  * NEVER prepend 'Wikipedia:' to the subject when building a start_url. \n"
            "  * For Wikipedia crawling, valid article URLs follow the pattern: https://en.wikipedia.org/wiki/<Subject_with_Underscores> \n"
            " * Do NOT use namespaces like 'Wikipedia:', 'Help:', 'Template:', etc. \n"
            "\n"
            "Only call tools when all parameters are present. Always prefer acting over hesitating or delaying."
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
                            "expression": {
                                "type": "string",
                                "description": "Math expression to evaluate, e.g., a * b or (a + b)."
                            }
                        },
                        "required": ["expression"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scrapWeatherFunc",
                    "description": "Find relevant information about the weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_name": {
                                "type": "string",
                                "description": "City name to retrieve weather for."
                            },
                            "day": {
                                "type": "string",
                                "description": "Specific day, like: Today, Tomorrow."
                            },
                            "degreesType": {
                                "type": "string",
                                "description": "Celsius or Fahrenheit."
                            }
                        },
                        "required": ["city_name", "day", "degreesType"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "crawlSubjectFunc",
                    "description": "Crawl Wikipedia for pages related to a specific subject starting from a given URL.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_url": {
                                "type": "string",
                                "description": "The Wikipedia URL to start crawling from."
                            },
                            "subject": {
                                "type": "string",
                                "description": "The subject or keyword to filter relevant pages."
                            }
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

    def scrapWeatherFunc(self, city_name: str, day: str, degreesType: str) -> str:
        units = "metric" if degreesType.lower() == "celsius" else "imperial"
        load_dotenv(dotenv_path="../.env")
        api_key = os.getenv("API_KEY_METHEO")
        
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units={units}&appid={api_key}"
        try:
            res = requests.get(weather_url)
            if res.status_code != 200:
                return f"Failed to retrieve weather. Status code: {res.status_code}"
            data = res.json()
            temp = data['main']['temp']
            condition = data['weather'][0]['description']
            degree_label = "Celsius" if units == "metric" else "Fahrenheit"
            return f"The weather in {city_name} {day.lower()} is {temp} {degree_label}, {condition}"
        except Exception as e:
            return f"Error: {e}"

    def crawlSubjectFunc(self, start_url: str, subject: str) -> str:
        crawler = Crawler(start_url, subject=subject)
        asyncio.run(crawler.multi_crawler_async(start_url, max_depth=0, tolerant_depth=1))
        crawler.save_links_to_json("linksJson.json")
        return f"Crawling complete. Results saved to linksJson.json."

    def chat(self):
        while True:
            user_input = input("User: ")
            if user_input.lower() in ['exit', 'quit']:
                break

            self.payload["messages"].append({"role": "user", "content": user_input})
            res = requests.post(self.url, json=self.payload)
            message = res.json()["choices"][0]["message"]

            if "content" in message:
                print("Model:", message["content"])
                self.payload["messages"].append(message)

            elif "tool_calls" in message:
                print("Model wants to call a function.")
                self.payload["messages"].append(message)

                tool_messages = []
                seen_expressions = set()

                for call in message["tool_calls"]:
                    tool_name = call["function"]["name"]
                    args = json.loads(call["function"]["arguments"])

                    if tool_name == "calculateFunc":
                        expr = args["expression"]
                        if expr not in seen_expressions:
                            result = self.calculateFunc(expr)
                            seen_expressions.add(expr)
                    elif tool_name == "scrapWeatherFunc":
                        result = self.scrapWeatherFunc(args["city_name"], args["day"], args["degreesType"])
                    elif tool_name == "crawlSubjectFunc":
                        start_url = args.get("start_url")
                        subject = args.get("subject")
                        if start_url and subject:
                            result = self.crawlSubjectFunc(start_url, subject)
                        else:
                            result = "Missing `start_url` or `subject` for crawlSubjectFunc"
                    else:
                        result = f"Unknown tool: {tool_name}"

                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": tool_name,
                        "content": result
                    })

                self.payload["messages"].extend(tool_messages)

                res2 = requests.post(self.url, json=self.payload)
                follow_up = res2.json()["choices"][0]["message"]
                if "content" in follow_up:
                    print("Model:", follow_up["content"])
                    self.payload["messages"].append(follow_up)
                elif "tool_calls" in follow_up:
                    print("Model wants to call another function again.")
                    self.payload["messages"].append(follow_up)
