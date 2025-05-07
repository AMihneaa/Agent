from __init__ import Crawler
from dynamicScraping import DynamicScraping
import asyncio
import json

async def mainCrawler():
    crawler = Crawler("https://en.wikipedia.org/wiki/Romania", subject="Romania President")
    await crawler.multi_crawler_async("https://en.wikipedia.org/wiki/Romania", max_depth=1)
    crawler.save_links_to_json("test.json")

async def dynamicScraping():
    scraper = DynamicScraping(base_url="https://www.emag.ro/laptopuri/")
    await scraper.init_browser()
    await scraper.navigate()
    
    filters = await scraper.extract_filters()
    # print("Filters:", filters)

    target_labels = ["AMD Ryzen™ 5", "4 GB"]

    with open("filter.json", "r", encoding="utf-8") as f:
        json_filters = json.load(f)

    results = []

    for category in json_filters:
        for option in category.get("options", []):
            label = option.get("label", "").strip()
            for target in target_labels:
                if target.lower() in label.lower():
                    results.append({
                        "label": label,
                        "url": option.get("url")
                    })

    print(f'{results} \n \n\n\n\n')

    result = scraper.build_filters("https://www.emag.ro/laptopuri", results)

    print(result)

    products = await scraper.extract_products()
    print("Products:", products[:10])  

    await scraper.close()

    scraper.saveToJson()

if __name__ == "__main__":
    # asyncio.run(mainCrawler())
    asyncio.run(dynamicScraping())
