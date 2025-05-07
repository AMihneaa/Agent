from __init__ import Crawler
from dynamicScraping import DynamicScraping
import asyncio
import json

async def mainCrawler():
    crawler = Crawler("https://en.wikipedia.org/wiki/Romania", subject="Romania President")
    await crawler.multi_crawler_async("https://en.wikipedia.org/wiki/Romania", max_depth=1)
    crawler.save_links_to_json("test.json")

async def dynamicScraping():
    async with DynamicScraping(base_url="https://www.emag.ro/laptopuri/") as scraper:
        filters = await scraper.extract_filters()

        target_labels = ["AMD Ryzen™ 5", "4 GB"]

        with open("filter.json", "r", encoding="utf-8") as f:
            json_filters = json.load(f)

        results = []

        for category in json_filters:
            for option in category.get("options", []):
                label = option.get("label", "").strip()
                if any(target.lower() in label.lower() for target in target_labels):
                    results.append({
                        "label": label,
                        "url": option.get("url")
                    })

        combined_url = scraper.build_filters("https://www.emag.ro/laptopuri", results)
        print("URL cu filtre combinate:", combined_url)

        scraper.saveToJson()


if __name__ == "__main__":
    # asyncio.run(mainCrawler())
    asyncio.run(dynamicScraping())
