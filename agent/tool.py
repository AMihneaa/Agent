from agent.tool_function import calculateFunc, scrapWeatherFunc, crawlSubjectFunc

tool_functions = {
    "calculateFunc": calculateFunc,
    "scrapWeatherFunc": scrapWeatherFunc,
    "crawlSubjectFunc": crawlSubjectFunc
}

tools = {
    "calculateFunc": {
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
    "scrapWeatherFunc": {
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
    "crawlSubjectFunc": {
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
}
