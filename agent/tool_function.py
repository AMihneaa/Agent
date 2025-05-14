import os
import httpx
import json
from dotenv import load_dotenv
from crawler.__init__ import Crawler

async def scrapWeatherFunc(city_name: str, day: str, degreesType: str) -> str:
    units = "metric" if degreesType.lower() == "celsius" else "imperial"
    load_dotenv(dotenv_path="../.env")
    api_key = os.getenv("API_KEY_METHEO")
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&units={units}&appid={api_key}"

    async with httpx.AsyncClient() as client:
        res = await client.get(weather_url)
        if res.status_code != 200:
            return f"Failed to retrieve weather. Status code: {res.status_code}"
        data = res.json()
        temp = data['main']['temp']
        condition = data['weather'][0]['description']
        degree_label = "Celsius" if units == "metric" else "Fahrenheit"
        return f"The weather in {city_name} {day.lower()} is {temp} {degree_label}, {condition}"

def calculateFunc(expression: str) -> str:
    try:
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

async def crawlSubjectFunc(start_url: str, subject: str) -> str:
    if not start_url.startswith("http"):
        start_url = f"https://en.wikipedia.org/wiki/{subject.replace(' ', '_')}"
    crawler = Crawler(start_url, subject=subject)
    await crawler.multi_crawler_async(start_url, max_depth=1, tolerant_depth=1)
    results = crawler.results
    if not results:
        return f"[TOOL_RESULT]No information found about '{subject}'.[END_TOOL_RESULT]"
    first = results[0]
    crawler.save_links_to_json("linksJson.json")
    return f"[TOOL_RESULT]{first['title']} ({first['url']})\nSnippet: {first['snippet'] if first['snippet'] else 'No description.'}[END_TOOL_RESULT]"
